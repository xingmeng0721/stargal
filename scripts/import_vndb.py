"""
VNDB 数据导入脚本 (PostgreSQL vndb -> 本项目 MySQL star_gal)
===========================================================

用途
----
把本地 PostgreSQL 的 vndb 公开数据，挑选「有用的核心信息」导入到本项目的
MySQL 数据库，用于功能测试。默认只导入一小批(评分最高的若干 VN)，
后期把 VN_LIMIT 调大或设为 None 即可逐步/完整导入。

导入内容(对应 star_gal 表)
--------------------------
- tags / tag_categories  <- vndb.tags (cont/ero/tech 三个分类)
- games                  <- vndb.vn + vn_titles (标题/原名/简介/评分/封面)
- game_aliases           <- vn_titles 各语言标题 + vn.alias
- game_images            <- vn_screenshots (拼接 VNDB 图片 URL)
- game_tags              <- tags_vn 聚合(同一 VN+标签的多用户投票求均值)
- characters / character_aliases / game_characters  <- chars/chars_names/chars_vns
- producers / game_producers                        <- producers/releases_producers
- staff / game_staff / game_seiyuu                  <- staff/vn_staff/vn_seiyuu
- releases / release_platforms / game_releases       <- releases/releases_vn

幂等(避免重复导入)
------------------
- 主记录(games/characters/producers/staff/releases)按 id 检测：
  IDEMPOTENT_MODE="skip" 时已存在则跳过；"update" 时刷新字段。
- 关联表(别名/截图/标签/角色关联等)对每个主记录「先删后插」，保证一致、不重复。
- id 沿用 vndb id 的数字部分，稳定可重复运行，支持增量扩量导入。

设计要点
--------
- vndbid -> 整型 id：直接取数字部分(v2002 -> 2002, g7 -> 7)。
  稳定、可重复运行(同一 VN 总是映射到同一 id)，便于增量导入。
- 幂等：每张表导入前用 INSERT ... ON DUPLICATE KEY UPDATE / 先删后插，
  重复运行不会产生脏数据。
- 评分换算：vndb 的 c_average 是 vote*100(如 905=9.05)，除以 100 存入。
- 描述去除 VNDB 的 BBCode 标记([b]..[/b] / [url=..]..[/url] 等)。
- 只读 PostgreSQL，不修改源库。

运行
----
  python -m scripts.import_vndb
或
  python scripts/import_vndb.py

可调参数见下方 CONFIG。
"""

import re
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras
import pymysql

# 让脚本能 import app.*（读取 MySQL 连接配置）
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings  # noqa: E402

# ============================= CONFIG =============================
# PostgreSQL(vndb 源库)连接
PG_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "vndb",
    "user": "postgres",
    "password": "123456",
}

# 导入多少个 VN（按热度排序）。测试用小批量；设为 None 表示不限制(完整导入)。
VN_LIMIT = 10

# 只导入投票数达到该阈值的 VN，过滤掉「1-2 票就 10 分」的冷门噪音条目，
# 让测试数据是真正知名的作品(Steins;Gate 等)。完整导入时可设为 0。
MIN_VOTECOUNT = 50

# 每个 VN 最多导入多少张截图，避免测试库膨胀。
SCREENSHOTS_PER_VN = 6

# game_tags：每个 VN 只取投票数较多、权重较高的前 N 个标签
TAGS_PER_VN = 15

# 上传者(games.uploader_id)。设为 None 表示不关联用户。
DEFAULT_UPLOADER_ID = None

# 幂等模式：
#   "skip"   = 已存在的主记录(同 id)跳过，不重复导入(增量导入推荐)
#   "update" = 已存在则更新主记录字段(刷新数据用)
# 关联表(别名/截图/标签等)始终「先删后插」以保证一致。
IDEMPOTENT_MODE = "skip"
# =================================================================


def parse_vndb_date(val):
    """vndb 的 released 是 YYYYMMDD 整数，含特殊值：
    99999999=TBA/未知；月或日为 99 表示该部分未知。
    返回 datetime.date 或 None(无法构成有效日期时)。
    """
    import datetime as _dt
    if not val or val >= 99999999:
        return None
    s = f"{int(val):08d}"
    year, month, day = int(s[:4]), int(s[4:6]), int(s[6:8])
    if year < 1000:
        return None
    if month == 99 or month == 0:
        month = 1
    if day == 99 or day == 0:
        day = 1
    try:
        return _dt.date(year, month, day)
    except ValueError:
        return None


# vndb char_sex(''/m/f/b/n) -> CharSex 成员名
CHAR_SEX_MAP = {"": "UNKNOWN", "m": "MALE", "f": "FEMALE", "b": "BOTH", "n": "NONE"}
# vndb char_role -> CharRole 成员名
CHAR_ROLE_MAP = {"main": "MAIN", "primary": "PRIMARY", "side": "SIDE", "appears": "APPEARS"}
# vndb producer_type -> ProducerType 成员名
PRODUCER_TYPE_MAP = {"co": "COMPANY", "in": "INDIVIDUAL", "ng": "AMATEUR"}
# vndb credit_type -> CreditType 成员名
CREDIT_TYPE_MAP = {
    "scenario": "SCENARIO", "chardesign": "CHARDESIGN", "art": "ART", "music": "MUSIC",
    "songs": "SONGS", "director": "DIRECTOR", "translator": "TRANSLATOR",
    "editor": "EDITOR", "qa": "QA", "staff": "STAFF",
}


# games.status：SQLAlchemy Enum 在 MySQL 中存「成员名」字符串，而非整数
GAME_STATUS_PUBLISHED = "PUBLISHED"
# tag 大类(对应 app.models.tag.TagType 的成员名)
TAGTYPE_CONTENT, TAGTYPE_MOE, TAGTYPE_TECH, TAGTYPE_OTHER = "CONTENT", "MOE", "TECH", "OTHER"

# vndb tag.cat -> 我们的分类(名称, TagType)
TAG_CAT_MAP = {
    "cont": ("剧情内容", TAGTYPE_CONTENT),
    "ero":  ("成人内容", TAGTYPE_OTHER),
    "tech": ("技术制作", TAGTYPE_TECH),
}

# 主标题语言优先级：优先中文，其次英文、日文
TITLE_LANG_PRIORITY = ["zh-Hans", "zh-Hant", "en", "ja"]

_BBCODE_RE = re.compile(r"\[/?(?:b|i|u|s|url|spoiler|quote|code|raw)[^\]]*\]", re.IGNORECASE)


def vndbid_to_int(vid: str) -> int:
    """v2002 -> 2002, g7 -> 7。取末尾连续数字。"""
    m = re.search(r"(\d+)$", vid)
    return int(m.group(1)) if m else 0


def strip_bbcode(text: str | None) -> str | None:
    if not text:
        return text
    return _BBCODE_RE.sub("", text).strip()


def vndb_image_url(img_id: str | None) -> str | None:
    """cv77819 -> https://t.vndb.org/cv/19/77819.jpg ; sf41868 -> .../sf/68/41868.jpg

    VNDB 图片 CDN 规则：类型前缀(cv/sf) / 数字后两位 / 完整数字.jpg
    """
    if not img_id:
        return None
    m = re.match(r"([a-z]+)(\d+)", img_id)
    if not m:
        return None
    prefix, num = m.group(1), m.group(2)
    return f"https://t.vndb.org/{prefix}/{num[-2:].zfill(2)}/{num}.jpg"


def get_mysql_conn():
    return pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DB,
        charset="utf8mb4",
        autocommit=False,
    )


def fetch_existing_ids(mcur, table, ids):
    """返回 ids 中已存在于 table 的 id 集合(用于幂等跳过)。"""
    if not ids:
        return set()
    fmt = ",".join(["%s"] * len(ids))
    mcur.execute(f"SELECT id FROM {table} WHERE id IN ({fmt})", tuple(ids))
    return {row[0] for row in mcur.fetchall()}


def import_tags(pg, my):
    """导入标签分类与标签。"""
    pcur = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    mcur = my.cursor()

    # 1) 分类：固定三类，用稳定 id(1/2/3)
    cat_id_by_cat = {}
    for i, (cat, (name, ttype)) in enumerate(TAG_CAT_MAP.items(), start=1):
        cat_id_by_cat[cat] = i
        mcur.execute(
            "INSERT INTO tag_categories (id, name, type, sort_order) VALUES (%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE name=VALUES(name), type=VALUES(type)",
            (i, name, ttype, i),
        )

    # 2) 标签本体(只导入可搜索的标签，减少噪音)
    pcur.execute("SELECT id, cat, name, description FROM tags WHERE searchable = true")
    rows = pcur.fetchall()
    count = 0
    for r in rows:
        tid = vndbid_to_int(r["id"])
        cat_id = cat_id_by_cat.get(r["cat"])
        name = (r["name"] or "")[:50]
        desc = strip_bbcode(r["description"])
        if desc:
            desc = desc[:255]
        mcur.execute(
            "INSERT INTO tags (id, name, description, category_id, usage_count) "
            "VALUES (%s,%s,%s,%s,0) "
            "ON DUPLICATE KEY UPDATE name=VALUES(name), category_id=VALUES(category_id)",
            (tid, name, desc, cat_id),
        )
        count += 1
    my.commit()
    print(f"[tags] 分类 {len(TAG_CAT_MAP)} 个, 标签 {count} 个")
    pcur.close()
    mcur.close()


def pick_titles(pg, vids):
    """批量取每个 VN 的标题(各语言)。返回 {vid: [(lang, official, title, latin), ...]}。"""
    pcur = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    pcur.execute(
        "SELECT id, lang, official, title, latin FROM vn_titles WHERE id = ANY(%s)",
        (vids,),
    )
    out: dict[str, list] = {}
    for r in pcur.fetchall():
        out.setdefault(r["id"], []).append(
            (r["lang"], r["official"], r["title"], r["latin"])
        )
    pcur.close()
    return out


def pick_main_title(titles: list) -> tuple[str | None, str | None]:
    """从标题列表里挑主标题与原名。返回 (main_title, original_title)。"""
    by_lang = {lang: (title, latin) for (lang, official, title, latin) in titles}
    main = None
    for lang in TITLE_LANG_PRIORITY:
        if lang in by_lang and by_lang[lang][0]:
            main = by_lang[lang][0]
            break
    if main is None and titles:
        main = titles[0][2]  # 兜底取第一个
    # 原名优先日文，其次第一个
    original = by_lang.get("ja", (None, None))[0]
    return main, original


def import_games(pg, my):
    """导入 VN 及其别名、截图、开发商、game_tags。"""
    pcur = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    mcur = my.cursor()

    limit_sql = f"LIMIT {VN_LIMIT}" if VN_LIMIT else ""
    pcur.execute(
        f"""
        SELECT id, olang, image, c_image, c_votecount, c_average, devstatus,
               alias, description
        FROM vn
        WHERE c_average IS NOT NULL AND c_votecount >= {MIN_VOTECOUNT}
        ORDER BY c_average DESC
        {limit_sql}
        """
    )
    vns = pcur.fetchall()
    vids = [v["id"] for v in vns]
    if not vids:
        print("[games] 源库没有可导入的 VN")
        return []

    # 幂等：查出已存在的 game id
    all_gids = [vndbid_to_int(v["id"]) for v in vns]
    existing = fetch_existing_ids(mcur, "games", all_gids)

    titles_map = pick_titles(pg, vids)

    # devstatus: 0=finished,1=ongoing,2=cancelled -> 我们统一标记为已发布(测试用)
    game_count = alias_count = img_count = skipped = 0
    for v in vns:
        gid = vndbid_to_int(v["id"])
        if gid in existing and IDEMPOTENT_MODE == "skip":
            skipped += 1
            continue
        titles = titles_map.get(v["id"], [])
        main_title, original_title = pick_main_title(titles)
        if not main_title:
            main_title = v["id"]  # 极端兜底
        rating = round((v["c_average"] or 0) / 100.0, 2)
        cover = vndb_image_url(v["image"] or v["c_image"])
        desc = strip_bbcode(v["description"])

        mcur.execute(
            """
            INSERT INTO games
                (id, title, original_title, description, description_en, cover_url,
                 status, uploader_id, rating_avg, rating_count, view_count,
                 favorite_count, download_count, comment_count, nsfw,
                 vndb_id, vndb_score, is_deleted)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,0,0,0,%s,%s,0)
            ON DUPLICATE KEY UPDATE
                title=VALUES(title), original_title=VALUES(original_title),
                description=VALUES(description), description_en=VALUES(description_en),
                cover_url=VALUES(cover_url),
                rating_avg=VALUES(rating_avg), rating_count=VALUES(rating_count),
                vndb_id=VALUES(vndb_id), vndb_score=VALUES(vndb_score)
            """,
            (
                gid, main_title[:200], (original_title or None) and original_title[:200],
                desc, desc, cover, GAME_STATUS_PUBLISHED, DEFAULT_UPLOADER_ID,
                rating, v["c_votecount"] or 0,
                v["id"], rating,
            ),
        )
        game_count += 1

        # —— 别名：各语言标题 + vn.alias 换行分隔 ——
        mcur.execute("DELETE FROM game_aliases WHERE game_id=%s", (gid,))
        seen = set()
        alias_rows = []
        for (lang, official, title, latin) in titles:
            for val in (title, latin):
                if val and val not in seen:
                    seen.add(val)
                    alias_rows.append((gid, val[:200], lang[:10] if lang else None))
        for a in (v["alias"] or "").split("\n"):
            a = a.strip()
            if a and a not in seen:
                seen.add(a)
                alias_rows.append((gid, a[:200], None))
        if alias_rows:
            mcur.executemany(
                "INSERT INTO game_aliases (game_id, alias, lang) VALUES (%s,%s,%s)",
                alias_rows,
            )
            alias_count += len(alias_rows)

        # —— 截图 ——
        mcur.execute("DELETE FROM game_images WHERE game_id=%s", (gid,))
        pcur.execute(
            "SELECT scr FROM vn_screenshots WHERE id=%s LIMIT %s",
            (v["id"], SCREENSHOTS_PER_VN),
        )
        scr_rows = []
        for i, s in enumerate(pcur.fetchall()):
            url = vndb_image_url(s["scr"])
            if url:
                scr_rows.append((gid, url, i))
        if scr_rows:
            mcur.executemany(
                "INSERT INTO game_images (game_id, url, sort_order) VALUES (%s,%s,%s)",
                scr_rows,
            )
            img_count += len(scr_rows)

    my.commit()
    print(f"[games] 导入 {game_count} 个游戏, {alias_count} 条别名, {img_count} 张截图 (跳过已存在 {skipped})")

    # —— 开发商：取每个 VN 的主要 developer 写回 games.developer ——
    pcur.execute(
        """
        SELECT DISTINCT ON (rv.vid) rv.vid, p.name
        FROM releases_vn rv
        JOIN releases_producers rp ON rp.id = rv.id AND rp.developer = true
        JOIN producers p ON p.id = rp.pid
        WHERE rv.vid = ANY(%s)
        ORDER BY rv.vid, p.name
        """,
        (vids,),
    )
    dev_count = 0
    for r in pcur.fetchall():
        mcur.execute(
            "UPDATE games SET developer=%s WHERE id=%s",
            ((r["name"] or "")[:100], vndbid_to_int(r["vid"])),
        )
        dev_count += 1
    my.commit()
    print(f"[games] 回填开发商 {dev_count} 个")

    # —— game_tags：聚合 tags_vn(同一 vid+tag 多用户投票) ——
    import_game_tags(pg, my, vids)

    pcur.close()
    mcur.close()
    return vids


def import_game_tags(pg, my, vids):
    """聚合标签投票并写入 game_tags，同时更新 tags.usage_count。"""
    pcur = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    mcur = my.cursor()

    # 已导入的标签 id 集合(只关联存在的标签)
    mcur.execute("SELECT id FROM tags")
    valid_tag_ids = {row[0] for row in mcur.fetchall()}

    # 聚合：每个 VN+标签的平均票数(vote 范围 -3..3)与投票人数
    pcur.execute(
        """
        SELECT vid, tag, AVG(vote)::float AS avg_vote, COUNT(*) AS votes
        FROM tags_vn
        WHERE vid = ANY(%s) AND ignore = false
        GROUP BY vid, tag
        HAVING AVG(vote) > 0
        """,
        (vids,),
    )
    rows = pcur.fetchall()

    # 按 VN 分组，取每个 VN 权重最高的前 TAGS_PER_VN 个
    by_vid: dict[str, list] = {}
    for r in rows:
        tid = vndbid_to_int(r["tag"])
        if tid not in valid_tag_ids:
            continue
        by_vid.setdefault(r["vid"], []).append((tid, r["avg_vote"], r["votes"]))

    link_count = 0
    usage = {}
    for vid, lst in by_vid.items():
        gid = vndbid_to_int(vid)
        lst.sort(key=lambda x: (x[1], x[2]), reverse=True)
        mcur.execute("DELETE FROM game_tags WHERE game_id=%s", (gid,))
        batch = []
        for (tid, avg_vote, votes) in lst[:TAGS_PER_VN]:
            # weight 存成 0..100 的相关度(avg_vote 最大 3 -> 100)
            weight = round(min(avg_vote / 3.0, 1.0) * 100, 2)
            batch.append((gid, tid, weight, votes))
            usage[tid] = usage.get(tid, 0) + 1
        if batch:
            mcur.executemany(
                "INSERT INTO game_tags (game_id, tag_id, weight, vote_count) "
                "VALUES (%s,%s,%s,%s)",
                batch,
            )
            link_count += len(batch)

    # 更新标签使用计数
    for tid, cnt in usage.items():
        mcur.execute("UPDATE tags SET usage_count=%s WHERE id=%s", (cnt, tid))

    my.commit()
    print(f"[game_tags] 导入 {link_count} 条游戏-标签关联")
    pcur.close()
    mcur.close()


def import_characters(pg, my, vids):
    """导入角色(只导入与已选 VN 关联的角色)及别名、游戏-角色关联、声优配音。"""
    pcur = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    mcur = my.cursor()

    # 1) 找出这些 VN 关联的角色 id + 在该 VN 中的定位
    pcur.execute(
        "SELECT DISTINCT id, vid, role FROM chars_vns WHERE vid = ANY(%s)", (vids,)
    )
    char_links = pcur.fetchall()
    cids = sorted({r["id"] for r in char_links})
    if not cids:
        print("[characters] 关联角色为空")
        pcur.close(); mcur.close()
        return

    # 2) 角色主体
    pcur.execute(
        "SELECT id, image, bloodt, sex, height, weight, birthday, description "
        "FROM chars WHERE id = ANY(%s)",
        (cids,),
    )
    chars = {r["id"]: r for r in pcur.fetchall()}

    # 角色主名：优先日文 chars_names，回退第一条
    pcur.execute(
        "SELECT id, lang, name, latin FROM chars_names WHERE id = ANY(%s)", (cids,)
    )
    names_map: dict[str, list] = {}
    for r in pcur.fetchall():
        names_map.setdefault(r["id"], []).append((r["lang"], r["name"], r["latin"]))

    all_cint = [vndbid_to_int(c) for c in cids]
    existing = fetch_existing_ids(mcur, "characters", all_cint)

    char_count = alias_count = 0
    for cid in cids:
        cint = vndbid_to_int(cid)
        if cint in existing and IDEMPOTENT_MODE == "skip":
            continue
        c = chars.get(cid)
        names = names_map.get(cid, [])
        # 主名：优先日文
        main_name = main_latin = None
        for (lang, name, latin) in names:
            if lang == "ja":
                main_name, main_latin = name, latin
                break
        if main_name is None and names:
            main_name, main_latin = names[0][1], names[0][2]
        if not main_name:
            main_name = cid
        # 中文名(name_cn)：取 zh-Hans/zh-Hant 名(VNDB 多数角色没有,留空由 BGM 后续补)
        name_cn = None
        for (lang, name, latin) in names:
            if lang in ("zh-Hans", "zh-Hant") and name:
                name_cn = name
                break
        sex = CHAR_SEX_MAP.get((c["sex"] if c else "") or "", "UNKNOWN")
        mcur.execute(
            """
            INSERT INTO characters
                (id, name, name_cn, description, image_url, sex,
                 blood_type, height, weight, birthday, is_deleted)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
            ON DUPLICATE KEY UPDATE
                name=VALUES(name), name_cn=VALUES(name_cn),
                description=VALUES(description), image_url=VALUES(image_url)
            """,
            (
                cint, main_name[:200], (name_cn or None) and name_cn[:200],
                strip_bbcode(c["description"]) if c else None,
                vndb_image_url(c["image"]) if c else None,
                sex,
                (c["bloodt"] if c and c["bloodt"] not in (None, "unknown") else None),
                (c["height"] if c and c["height"] else None),
                (c["weight"] if c else None),
                (c["birthday"] if c and c["birthday"] else None),
            ),
        )
        char_count += 1

        # 别名：所有语言名 + chars_alias(模型已去掉 lang 字段)
        mcur.execute("DELETE FROM character_aliases WHERE character_id=%s", (cint,))
        seen = set()
        arows = []
        for (lang, name, latin) in names:
            if name and name not in seen:
                seen.add(name)
                arows.append((cint, name[:200], (latin or None) and latin[:200]))
        if arows:
            mcur.executemany(
                "INSERT INTO character_aliases (character_id, name, latin) VALUES (%s,%s,%s)",
                arows,
            )
            alias_count += len(arows)
    my.commit()

    # 3) 游戏-角色关联(先删每个 VN 的旧关联)
    by_vid_chars: dict[str, list] = {}
    for r in char_links:
        by_vid_chars.setdefault(r["vid"], []).append((r["id"], r["role"]))
    valid_cids = set(all_cint)
    link_count = 0
    for vid, lst in by_vid_chars.items():
        gid = vndbid_to_int(vid)
        mcur.execute("DELETE FROM game_characters WHERE game_id=%s", (gid,))
        batch, seen = [], set()
        for (cid, role) in lst:
            cint = vndbid_to_int(cid)
            if cint not in valid_cids or cint in seen:
                continue
            seen.add(cint)
            batch.append((gid, cint, CHAR_ROLE_MAP.get(role, "APPEARS")))
        if batch:
            mcur.executemany(
                "INSERT INTO game_characters (game_id, character_id, role) VALUES (%s,%s,%s)",
                batch,
            )
            link_count += len(batch)
    my.commit()
    print(f"[characters] 导入 {char_count} 个角色, {alias_count} 条别名, {link_count} 条游戏-角色关联")
    pcur.close()
    mcur.close()


def import_producers(pg, my, vids):
    """导入厂商及游戏-厂商关联(区分开发/发行)。"""
    pcur = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    mcur = my.cursor()

    # 通过 releases_vn -> releases_producers 找到与这些 VN 相关的厂商
    pcur.execute(
        """
        SELECT DISTINCT rv.vid, rp.pid, rp.developer, rp.publisher
        FROM releases_vn rv
        JOIN releases_producers rp ON rp.id = rv.id
        WHERE rv.vid = ANY(%s)
        """,
        (vids,),
    )
    links = pcur.fetchall()
    pids = sorted({r["pid"] for r in links})
    if not pids:
        print("[producers] 关联厂商为空")
        pcur.close(); mcur.close()
        return

    pcur.execute(
        "SELECT id, type, lang, name, latin, alias, description FROM producers WHERE id = ANY(%s)",
        (pids,),
    )
    prods = {r["id"]: r for r in pcur.fetchall()}
    all_pint = [vndbid_to_int(p) for p in pids]
    existing = fetch_existing_ids(mcur, "producers", all_pint)

    prod_count = 0
    for pid in pids:
        pint = vndbid_to_int(pid)
        if pint in existing and IDEMPOTENT_MODE == "skip":
            continue
        p = prods.get(pid)
        if not p:
            continue
        mcur.execute(
            """
            INSERT INTO producers (id, name, latin_name, type, lang, aliases, description, is_deleted)
            VALUES (%s,%s,%s,%s,%s,%s,%s,0)
            ON DUPLICATE KEY UPDATE name=VALUES(name), latin_name=VALUES(latin_name),
                type=VALUES(type), description=VALUES(description)
            """,
            (
                pint, (p["name"] or "")[:200], (p["latin"] or None) and p["latin"][:200],
                PRODUCER_TYPE_MAP.get(p["type"], "COMPANY"), (p["lang"] or None),
                (p["alias"] or None), strip_bbcode(p["description"]),
            ),
        )
        prod_count += 1
    my.commit()

    # 游戏-厂商关联：同一 (vid,pid) 可能多条(多个 release)，聚合 developer/publisher
    agg: dict[tuple, list] = {}
    for r in links:
        key = (r["vid"], r["pid"])
        dev, pub = agg.get(key, (False, False))
        agg[key] = (dev or r["developer"], pub or r["publisher"])

    valid_pids = set(all_pint)
    by_vid: dict[str, list] = {}
    for (vid, pid), (dev, pub) in agg.items():
        by_vid.setdefault(vid, []).append((pid, dev, pub))

    link_count = 0
    for vid, lst in by_vid.items():
        gid = vndbid_to_int(vid)
        mcur.execute("DELETE FROM game_producers WHERE game_id=%s", (gid,))
        batch = []
        for (pid, dev, pub) in lst:
            pint = vndbid_to_int(pid)
            if pint in valid_pids:
                batch.append((gid, pint, 1 if dev else 0, 1 if pub else 0))
        if batch:
            mcur.executemany(
                "INSERT INTO game_producers (game_id, producer_id, is_developer, is_publisher) "
                "VALUES (%s,%s,%s,%s)",
                batch,
            )
            link_count += len(batch)
    my.commit()
    print(f"[producers] 导入 {prod_count} 个厂商, {link_count} 条游戏-厂商关联")
    pcur.close()
    mcur.close()


def import_staff(pg, my, vids):
    """
    导入制作人员(以 aid 为 id)及游戏-职务、游戏-声优关联。
    """
    pcur = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    mcur = my.cursor()

    # 职务关联
    pcur.execute(
        "SELECT id AS vid, aid, role, note FROM vn_staff WHERE id = ANY(%s)", (vids,)
    )
    staff_links = pcur.fetchall()
    # 声优关联
    pcur.execute(
        "SELECT id AS vid, cid, aid, note FROM vn_seiyuu WHERE id = ANY(%s)", (vids,)
    )
    seiyuu_links = pcur.fetchall()

    aids = sorted({r["aid"] for r in staff_links} | {r["aid"] for r in seiyuu_links})
    if not aids:
        print("[staff] 关联人员为空")
        pcur.close(); mcur.close()
        return

    # staff_alias 提供 aid->名字; staff 提供 gender/lang/description
    pcur.execute(
        """
        SELECT sa.aid, sa.name, sa.latin, s.gender, s.lang, s.description
        FROM staff_alias sa JOIN staff s ON s.id = sa.id
        WHERE sa.aid = ANY(%s)
        """,
        (aids,),
    )
    staff_map = {r["aid"]: r for r in pcur.fetchall()}
    existing = fetch_existing_ids(mcur, "staff", aids)

    staff_count = 0
    for aid in aids:
        if aid in existing and IDEMPOTENT_MODE == "skip":
            continue
        s = staff_map.get(aid)
        if not s:
            continue
        mcur.execute(
            """
            INSERT INTO staff (id, name, latin_name, lang, gender, description, is_deleted)
            VALUES (%s,%s,%s,%s,%s,%s,0)
            ON DUPLICATE KEY UPDATE name=VALUES(name), latin_name=VALUES(latin_name),
                description=VALUES(description)
            """,
            (
                aid, (s["name"] or "")[:200], (s["latin"] or None) and s["latin"][:200],
                (s["lang"] or None), (s["gender"] or None) or None,
                strip_bbcode(s["description"]),
            ),
        )
        staff_count += 1
    my.commit()

    valid_aids = set(staff_map.keys())

    # 游戏-职务
    by_vid_staff: dict[str, list] = {}
    for r in staff_links:
        by_vid_staff.setdefault(r["vid"], []).append((r["aid"], r["role"], r["note"]))
    gs_count = 0
    for vid, lst in by_vid_staff.items():
        gid = vndbid_to_int(vid)
        mcur.execute("DELETE FROM game_staff WHERE game_id=%s", (gid,))
        batch = []
        for (aid, role, note) in lst:
            if aid in valid_aids:
                batch.append((gid, aid, CREDIT_TYPE_MAP.get(role, "STAFF"), (note or None) and note[:255]))
        if batch:
            mcur.executemany(
                "INSERT INTO game_staff (game_id, staff_id, role, note) VALUES (%s,%s,%s,%s)",
                batch,
            )
            gs_count += len(batch)
    my.commit()

    # 游戏-声优(需要角色已导入；只关联已存在的角色)
    mcur.execute("SELECT id FROM characters")
    valid_chars = {row[0] for row in mcur.fetchall()}
    by_vid_sei: dict[str, list] = {}
    for r in seiyuu_links:
        by_vid_sei.setdefault(r["vid"], []).append((r["aid"], r["cid"], r["note"]))
    sei_count = 0
    for vid, lst in by_vid_sei.items():
        gid = vndbid_to_int(vid)
        mcur.execute("DELETE FROM game_seiyuu WHERE game_id=%s", (gid,))
        batch, seen = [], set()
        for (aid, cid, note) in lst:
            cint = vndbid_to_int(cid)
            key = (aid, cint)
            if aid in valid_aids and cint in valid_chars and key not in seen:
                seen.add(key)
                batch.append((gid, aid, cint, (note or None) and note[:255]))
        if batch:
            mcur.executemany(
                "INSERT INTO game_seiyuu (game_id, staff_id, character_id, note) VALUES (%s,%s,%s,%s)",
                batch,
            )
            sei_count += len(batch)
    my.commit()
    print(f"[staff] 导入 {staff_count} 个人员, {gs_count} 条职务关联, {sei_count} 条声优配音")
    pcur.close()
    mcur.close()


def import_releases(pg, my, vids):
    """导入发行版本、平台、游戏-版本关联。"""
    pcur = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    mcur = my.cursor()

    # 与这些 VN 关联的 release
    pcur.execute(
        "SELECT id AS rid, vid, rtype FROM releases_vn WHERE vid = ANY(%s)", (vids,)
    )
    rel_links = pcur.fetchall()
    rids = sorted({r["rid"] for r in rel_links})
    if not rids:
        print("[releases] 关联版本为空")
        pcur.close(); mcur.close()
        return

    pcur.execute(
        "SELECT id, released, minage, patch, freeware, official, has_ero, notes "
        "FROM releases WHERE id = ANY(%s)",
        (rids,),
    )
    rels = {r["id"]: r for r in pcur.fetchall()}

    # 版本标题：取 releases_titles 任意一条(优先官方)
    pcur.execute(
        "SELECT DISTINCT ON (id) id, title FROM releases_titles WHERE id = ANY(%s) "
        "ORDER BY id, mtl ASC",
        (rids,),
    )
    title_map = {r["id"]: r["title"] for r in pcur.fetchall()}

    all_rint = [vndbid_to_int(r) for r in rids]
    existing = fetch_existing_ids(mcur, "releases", all_rint)

    rel_count = 0
    for rid in rids:
        rint = vndbid_to_int(rid)
        if rint in existing and IDEMPOTENT_MODE == "skip":
            continue
        r = rels.get(rid)
        if not r:
            continue
        mcur.execute(
            """
            INSERT INTO releases
                (id, title, released, minage, is_patch, is_freeware, is_official, has_ero, notes, is_deleted)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
            ON DUPLICATE KEY UPDATE title=VALUES(title), released=VALUES(released),
                minage=VALUES(minage), notes=VALUES(notes)
            """,
            (
                rint, (title_map.get(rid) or None) and title_map.get(rid)[:250],
                parse_vndb_date(r["released"]), r["minage"],
                1 if r["patch"] else 0, 1 if r["freeware"] else 0,
                1 if r["official"] else 0, 1 if r["has_ero"] else 0,
                strip_bbcode(r["notes"]),
            ),
        )
        rel_count += 1

        # 平台
        mcur.execute("DELETE FROM release_platforms WHERE release_id=%s", (rint,))
        pcur.execute("SELECT platform FROM releases_platforms WHERE id=%s", (rid,))
        prows = [(rint, pr["platform"][:10]) for pr in pcur.fetchall()]
        if prows:
            mcur.executemany(
                "INSERT INTO release_platforms (release_id, platform) VALUES (%s,%s)",
                prows,
            )
    my.commit()

    # 游戏-版本关联
    valid_rids = set(all_rint)
    by_vid: dict[str, list] = {}
    for r in rel_links:
        by_vid.setdefault(r["vid"], []).append((r["rid"], r["rtype"]))
    link_count = 0
    for vid, lst in by_vid.items():
        gid = vndbid_to_int(vid)
        mcur.execute("DELETE FROM game_releases WHERE game_id=%s", (gid,))
        batch = []
        for (rid, rtype) in lst:
            rint = vndbid_to_int(rid)
            if rint in valid_rids:
                batch.append((gid, rint, (rtype or None)))
        if batch:
            mcur.executemany(
                "INSERT INTO game_releases (game_id, release_id, rtype) VALUES (%s,%s,%s)",
                batch,
            )
            link_count += len(batch)
    my.commit()
    print(f"[releases] 导入 {rel_count} 个版本, {link_count} 条游戏-版本关联")
    pcur.close()
    mcur.close()


def main():
    print(f"开始导入 VNDB 数据 (VN_LIMIT={VN_LIMIT}) ...")
    pg = psycopg2.connect(**PG_CONFIG)
    pg.set_client_encoding("UTF8")
    my = get_mysql_conn()
    try:
        # 关闭外键检查，避免导入顺序问题(MySQL)
        with my.cursor() as c:
            c.execute("SET FOREIGN_KEY_CHECKS=0")
        import_tags(pg, my)
        vids = import_games(pg, my)
        if vids:
            import_characters(pg, my, vids)
            import_producers(pg, my, vids)
            import_staff(pg, my, vids)
            import_releases(pg, my, vids)
        with my.cursor() as c:
            c.execute("SET FOREIGN_KEY_CHECKS=1")
        my.commit()
        print("导入完成 [OK]")
    finally:
        pg.close()
        my.close()


if __name__ == "__main__":
    main()
