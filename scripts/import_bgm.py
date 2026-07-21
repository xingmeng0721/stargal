"""
BGM(Bangumi) 数据合并导入脚本
==============================

用途
----
把 Bangumi 归档(subject.jsonlines)中的「游戏(type=4)」数据，匹配到本项目里
**已由 VNDB 导入的游戏**，用 BGM 的信息补充/更新它们。核心目的：
- 给游戏补上「中文简介」(BGM 的 summary 基本是中文，正好补齐 VNDB 的英文简介)。
- 回填 BGM 评分/排名/NSFW/对应 BGM 条目ID。
- 顺便把 BGM 的别名(infobox 里的 别名)并入 game_aliases，增强搜索命中。

设计原则(以 VNDB 为基础)
------------------------
- 只更新「已存在(VNDB 已导入)的游戏」，不新建游戏 —— 即「在 vndb 里有收录的游戏」。
- VNDB 提供的字段(标题/英文简介/评分/封面等)保持不动，BGM 只填补空缺字段：
  - description_zh：BGM 中文简介
  - bgm_id / bgm_score / bgm_rank / nsfw：BGM 元数据
- 匹配方式：标题归一化后比对。
  BGM 的 name(原名,多为日文) / name_cn(中文名) 去匹配本库的
  原名(original_title)、标题(title)、以及 game_aliases 里的各种别名。

匹配可靠性说明
--------------
VNDB 与 BGM 没有公共数字ID(extlinks 里 bgmtv 链接极少)，因此用标题匹配。
归一化(NFKC + 去空格 + casefold)能消除全/半角、大小写、空格差异，
对 galgame 这种「原名唯一性高」的数据，标题匹配准确率很高。
匹配不到的 BGM 条目直接忽略(符合「其他数据忽略」的要求)。

运行
----
  python -m scripts.import_bgm

可调参数见 CONFIG。
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

import pymysql

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings  # noqa: E402

# ============================= CONFIG =============================
BGM_SUBJECT_FILE = r"E:\galdate\dump-2026-06-23.210442Z\subject.jsonlines"

# 测试用：最多处理(匹配成功)多少条就停止。设为 None 表示处理整个文件(完整导入)。
MATCH_LIMIT = 5

# 是否把 BGM 的别名并入 game_aliases(增强搜索)。
MERGE_ALIASES = True
# =================================================================

BGM_GAME_TYPE = 4  # subject.type==4 表示游戏


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


def norm_title(s: str | None) -> str | None:
    """标题归一化：NFKC(全角->半角)、去所有空白、casefold。用于跨库匹配。"""
    if not s:
        return None
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", "", s)
    s = s.strip().casefold()
    return s or None


def build_title_index(mcur) -> dict[str, int]:
    """从本库 games + game_aliases 构建 {归一化标题: game_id} 索引。

    冲突处理：同一归一化标题映射到多个 game 时，保留先出现的(原名/标题优先于别名)。
    """
    index: dict[str, int] = {}

    def put(title, gid):
        key = norm_title(title)
        if key and key not in index:
            index[key] = gid

    # 先放原名/标题(优先级高)
    mcur.execute("SELECT id, title, original_title FROM games WHERE is_deleted=0")
    for gid, title, original in mcur.fetchall():
        put(original, gid)
        put(title, gid)

    # 再放别名(优先级低，不覆盖已有)
    mcur.execute("SELECT game_id, alias FROM game_aliases")
    for gid, alias in mcur.fetchall():
        put(alias, gid)

    return index


# —— BGM infobox 解析(只取我们需要的：别名) ——
_ALIAS_BLOCK_RE = re.compile(r"\|别名=\{(.*?)\}", re.DOTALL)
_ALIAS_ITEM_RE = re.compile(r"\[([^\]|]+?)(?:\|[^\]]*)?\]")


def parse_bgm_aliases(infobox: str | None) -> list[str]:
    """从 BGM infobox 提取别名列表。

    infobox 形如：|别名={\n[シュタゲ]\n[石头门]\n}
    也可能是单行 |别名= xxx 形式，这里只解析常见的花括号列表形式。
    """
    if not infobox:
        return []
    m = _ALIAS_BLOCK_RE.search(infobox)
    if not m:
        return []
    return [a.strip() for a in _ALIAS_ITEM_RE.findall(m.group(1)) if a.strip()]


def merge_aliases(mcur, gid: int, aliases: list[str]):
    """把别名并入 game_aliases(去重，不重复插入已存在的)。"""
    if not aliases:
        return 0
    mcur.execute("SELECT alias FROM game_aliases WHERE game_id=%s", (gid,))
    existing = {norm_title(r[0]) for r in mcur.fetchall()}
    rows = []
    for a in aliases:
        k = norm_title(a)
        if k and k not in existing:
            existing.add(k)
            rows.append((gid, a[:200], None))
    if rows:
        mcur.executemany(
            "INSERT INTO game_aliases (game_id, alias, lang) VALUES (%s,%s,%s)", rows
        )
    return len(rows)


def main():
    print(f"开始合并 BGM 数据 (MATCH_LIMIT={MATCH_LIMIT}) ...")
    my = get_mysql_conn()
    mcur = my.cursor()

    index = build_title_index(mcur)
    print(f"已建立标题索引: {len(index)} 个标题键 (来自本库 VNDB 游戏)")
    if not index:
        print("本库还没有游戏，请先运行 VNDB 导入(scripts.import_vndb)。")
        my.close()
        return

    matched = 0
    scanned = 0
    alias_added = 0
    seen_gids: set[int] = set()

    with open(BGM_SUBJECT_FILE, encoding="utf-8") as f:
        for line in f:
            scanned += 1
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if o.get("type") != BGM_GAME_TYPE:
                continue

            # 用 原名 与 中文名 去匹配
            gid = None
            for cand in (o.get("name"), o.get("name_cn")):
                key = norm_title(cand)
                if key and key in index:
                    gid = index[key]
                    break
            if gid is None:
                continue
            if gid in seen_gids:
                continue  # 同一游戏只更新一次
            seen_gids.add(gid)

            summary = (o.get("summary") or "").strip() or None
            score = o.get("score")
            rank = o.get("rank")
            nsfw = 1 if o.get("nsfw") else 0
            bgm_id = o.get("id")

            # 更新游戏：中文简介 + BGM 元数据。
            # COALESCE 思路：description_zh 已有则不覆盖(尊重已有数据)；这里直接写入，
            # 因为 BGM 是中文简介的主要来源。description(兜底)若为空则用中文补。
            mcur.execute(
                """
                UPDATE games
                SET description_zh = %s,
                    description = COALESCE(NULLIF(description, ''), %s),
                    bgm_id = %s, bgm_score = %s, bgm_rank = %s, nsfw = %s
                WHERE id = %s
                """,
                (summary, summary, bgm_id, score, rank, nsfw, gid),
            )

            if MERGE_ALIASES:
                alias_added += merge_aliases(mcur, gid, parse_bgm_aliases(o.get("infobox")))

            matched += 1
            if matched <= 10:
                print(f"  匹配 game_id={gid} <- BGM[{bgm_id}] {o.get('name')} / {o.get('name_cn')} (score={score})")

            if MATCH_LIMIT and matched >= MATCH_LIMIT:
                break

    my.commit()
    print(f"扫描 {scanned} 行, 匹配并更新 {matched} 个游戏, 新增别名 {alias_added} 条")
    my.close()
    print("BGM 合并完成 [OK]")


if __name__ == "__main__":
    main()
