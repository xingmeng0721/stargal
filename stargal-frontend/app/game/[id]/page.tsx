"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { getGameDetail } from "@/lib/game"
import {
  getGameComments,
  postComment,
  addFavorite,
  removeFavorite,
  rateGame,
  getMyRating,
  setPlayStatus,
  getPlayStatus,
} from "@/lib/interaction"
import { useAuth } from "@/lib/auth-context"
import { getGamePublicSaves } from "@/lib/save"
import type { GameDetail } from "@/types/game"
import type { CommentOut, CommentCreate } from "@/types/interaction"
import type { SaveOut } from "@/types/save"
import StarRating from "@/components/StarRating"
import { PLAY_STATUS_LABELS } from "@/types/interaction"

export default function GameDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const { isLoggedIn, token } = useAuth()

  const [game, setGame] = useState<GameDetail | null>(null)
  const [comments, setComments] = useState<CommentOut[]>([])
  const [loading, setLoading] = useState(true)
  const [myScore, setMyScore] = useState<number | null>(null)
  const [myStatus, setMyStatus] = useState<number | null>(null)
  const [isFav, setIsFav] = useState(false)
  const [commentText, setCommentText] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [publicSaves, setPublicSaves] = useState<SaveOut[]>([])
  const [replyingTo, setReplyingTo] = useState<number | null>(null)
  const [replyText, setReplyText] = useState("")
  const [replySubmitting, setReplySubmitting] = useState(false)

  const gameId = parseInt(params.id, 10)

  // Load game + comments + user state
  useEffect(() => {
    if (!gameId || isNaN(gameId)) return

    const load = async () => {
      setLoading(true)
      try {
        const [gameData, commentData] = await Promise.all([
          getGameDetail(gameId, token ?? undefined),
          getGameComments(gameId),
        ])
        setGame(gameData)
        setComments(commentData.items)
        setIsFav(gameData.is_favorited ?? false)

        // Load public saves for this game
        try {
          const savesData = await getGamePublicSaves(gameId)
          setPublicSaves(savesData.items)
        } catch {
          // ignore
        }

        if (token) {
          const [rating, status] = await Promise.all([
            getMyRating(gameId, token),
            getPlayStatus(gameId, token),
          ])
          setMyScore(rating?.score ?? null)
          setMyStatus(status?.status ?? null)
        }
      } catch {
        // Game not found
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [gameId, token])

  // ── Actions ──────────────────────────────────────────────

  const handleRate = async (score: number) => {
    if (!token) {
      router.push("/login")
      return
    }
    try {
      const result = await rateGame(gameId, score, token)
      setMyScore(result.score)
      // Refresh game to get updated avg
      const updated = await getGameDetail(gameId, token)
      setGame(updated)
    } catch {
      // ignore
    }
  }

  const handleFavorite = async () => {
    if (!token) {
      router.push("/login")
      return
    }
    try {
      if (isFav) {
        await removeFavorite(gameId, token)
        setIsFav(false)
        setGame((prev) =>
          prev ? { ...prev, favorite_count: Math.max(prev.favorite_count - 1, 0) } : prev
        )
      } else {
        await addFavorite(gameId, token)
        setIsFav(true)
        setGame((prev) =>
          prev ? { ...prev, favorite_count: prev.favorite_count + 1 } : prev
        )
      }
    } catch {
      // ignore
    }
  }

  const handlePlayStatus = async (status: number) => {
    if (!token) {
      router.push("/login")
      return
    }
    try {
      await setPlayStatus(gameId, status, token)
      setMyStatus(status)
    } catch {
      // ignore
    }
  }

  const handleComment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !commentText.trim()) return
    setSubmitting(true)
    try {
      const data: CommentCreate = { content: commentText.trim() }
      const comment = await postComment(gameId, data, token)
      setComments((prev) => [comment, ...prev])
      setCommentText("")
    } catch {
      // ignore
    } finally {
      setSubmitting(false)
    }
  }

  const handleReply = async (parentCommentId: number, replyToUsername?: string) => {
    if (!token || !replyText.trim()) return
    setReplySubmitting(true)
    try {
      const prefix = replyToUsername ? `@${replyToUsername} ` : ""
      const data: CommentCreate = { content: prefix + replyText.trim(), parent_id: parentCommentId }
      const reply = await postComment(gameId, data, token)
      // Append reply to the top-level comment's replies array
      setComments((prev) =>
        prev.map((c) =>
          c.id === parentCommentId
            ? { ...c, replies: [...c.replies, reply], reply_count: c.reply_count + 1 }
            : c
        )
      )
      setReplyText("")
      setReplyingTo(null)
    } catch {
      // ignore
    } finally {
      setReplySubmitting(false)
    }
  }

  // ── Render ───────────────────────────────────────────────

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="flex gap-8">
            <div className="h-80 w-56 shrink-0 rounded-2xl bg-zinc-800" />
            <div className="flex-1 space-y-4">
              <div className="h-8 w-3/4 rounded bg-zinc-800" />
              <div className="h-4 w-1/2 rounded bg-zinc-800" />
              <div className="h-24 w-full rounded bg-zinc-800" />
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!game) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-zinc-400">游戏不存在或已下架</p>
        <Link href="/" className="mt-4 text-sm text-violet-400 hover:underline">
          返回首页
        </Link>
      </div>
    )
  }

  const description = game.description_zh || game.description || game.description_en || game.description_ja

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      {/* Breadcrumb */}
      <nav className="mb-4 flex items-center gap-2 text-xs text-zinc-500">
        <Link href="/" className="hover:text-zinc-300">首页</Link>
        <span>/</span>
        <span className="text-zinc-300">{game.title}</span>
      </nav>

      {/* Hero section */}
      <div className="flex flex-col gap-8 md:flex-row">
        {/* Cover */}
        <div className="w-full shrink-0 md:w-56">
          <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900">
            {game.cover_url ? (
              <img
                src={game.cover_url}
                alt={game.title}
                className="aspect-[3/4] w-full object-cover"
              />
            ) : (
              <div className="flex aspect-[3/4] w-full items-center justify-center bg-zinc-800">
                <svg className="h-16 w-16 text-zinc-700" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
                </svg>
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold text-zinc-100">{game.title}</h1>
          {game.original_title && game.original_title !== game.title && (
            <p className="mt-1 text-sm text-zinc-500">{game.original_title}</p>
          )}

          {/* Meta grid */}
          <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
            {game.developer && (
              <div>
                <span className="text-zinc-500">开发商</span>
                <p className="text-zinc-200">{game.developer}</p>
              </div>
            )}
            {game.publisher && (
              <div>
                <span className="text-zinc-500">发行商</span>
                <p className="text-zinc-200">{game.publisher}</p>
              </div>
            )}
            {game.release_date && (
              <div>
                <span className="text-zinc-500">发售日</span>
                <p className="text-zinc-200">{game.release_date}</p>
              </div>
            )}
          </div>

          {/* Scores */}
          <div className="mt-4 flex flex-wrap items-center gap-4">
            {game.bgm_score && (
              <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2">
                <span className="text-xs text-zinc-500">BGM</span>
                <span className="text-lg font-bold text-amber-400">
                  {Number(game.bgm_score).toFixed(1)}
                </span>
                {game.bgm_rank && (
                  <span className="text-xs text-zinc-500">#{game.bgm_rank}</span>
                )}
              </div>
            )}
            {game.vndb_score && (
              <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2">
                <span className="text-xs text-zinc-500">VNDB</span>
                <span className="text-lg font-bold text-emerald-400">
                  {Number(game.vndb_score).toFixed(1)}
                </span>
              </div>
            )}
            <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2">
              <span className="text-xs text-zinc-500">社区</span>
              <StarRating value={Number(game.rating_avg)} size="sm" readonly />
              <span className="text-sm font-medium text-zinc-300">
                {Number(game.rating_avg).toFixed(1)}
              </span>
              <span className="text-xs text-zinc-500">({game.rating_count})</span>
            </div>
          </div>

          {/* Tags */}
          {game.tags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {game.tags.map((tag) => (
                <Link
                  key={tag.id}
                  href={`/?tag=${encodeURIComponent(tag.name)}`}
                  className="rounded-lg bg-zinc-800 px-2.5 py-1 text-xs text-zinc-300 transition hover:bg-violet-900 hover:text-violet-300"
                >
                  {tag.name}
                </Link>
              ))}
            </div>
          )}

          {/* Action buttons */}
          <div className="mt-5 flex flex-wrap gap-2">
            <button
              onClick={handleFavorite}
              className={`flex items-center gap-1.5 rounded-xl border px-4 py-2 text-sm font-medium transition ${
                isFav
                  ? "border-pink-800 bg-pink-950 text-pink-300"
                  : "border-zinc-700 text-zinc-300 hover:border-pink-700 hover:text-pink-300"
              }`}
            >
              <svg className="h-4 w-4" fill={isFav ? "currentColor" : "none"} viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
              </svg>
              {isFav ? "已收藏" : "收藏"}
            </button>

            {/* Play status */}
            <div className="flex items-center gap-1 rounded-xl border border-zinc-700 p-1">
              {Object.entries(PLAY_STATUS_LABELS).map(([key, label]) => {
                const statusNum = parseInt(key, 10)
                return (
                  <button
                    key={key}
                    onClick={() => handlePlayStatus(statusNum)}
                    className={`rounded-lg px-2.5 py-1.5 text-xs transition ${
                      myStatus === statusNum
                        ? "bg-violet-600 text-white"
                        : "text-zinc-400 hover:text-white"
                    }`}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* My rating */}
          <div className="mt-4 flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3">
            <span className="text-sm text-zinc-400">我的评分</span>
            <StarRating
              value={myScore ?? 0}
              size="md"
              onChange={handleRate}
            />
            {myScore !== null && (
              <span className="text-sm font-medium text-amber-400">{Number(myScore).toFixed(1)}</span>
            )}
          </div>

          {/* Stats */}
          <div className="mt-4 flex gap-4 text-xs text-zinc-500">
            <span>{game.view_count} 浏览</span>
            <span>{game.favorite_count} 收藏</span>
            <span>{game.download_count} 下载</span>
            <span>{game.comment_count} 评论</span>
          </div>
        </div>
      </div>

      {/* Description */}
      {description && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold text-zinc-200">简介</h2>
          <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-400">
            {description}
          </p>
        </section>
      )}

      {/* Aliases */}
      {game.aliases.length > 0 && (
        <section className="mt-6">
          <h2 className="mb-3 text-lg font-semibold text-zinc-200">别名</h2>
          <div className="flex flex-wrap gap-2">
            {game.aliases.map((a) => (
              <span key={a.id} className="rounded-lg bg-zinc-800 px-3 py-1.5 text-sm text-zinc-300">
                {a.alias}
                {a.lang && <span className="ml-1 text-xs text-zinc-500">({a.lang})</span>}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Screenshots */}
      {game.images.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold text-zinc-200">截图</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {game.images.map((img) => (
              <button
                key={img.id}
                onClick={() => setSelectedImage(img.url)}
                className="overflow-hidden rounded-xl border border-zinc-800 transition hover:border-zinc-600"
              >
                <img
                  src={img.url}
                  alt=""
                  className="aspect-video w-full object-cover transition hover:scale-105"
                  loading="lazy"
                />
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Lightbox */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={() => setSelectedImage(null)}
        >
          <img
            src={selectedImage}
            alt=""
            className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain"
          />
          <button className="absolute right-4 top-4 rounded-full bg-zinc-800 p-2 text-white">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Resources */}
      {game.resources.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold text-zinc-200">资源下载</h2>
          <div className="space-y-2">
            {game.resources.map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-zinc-200">{r.title}</p>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {r.file_name} &middot;{" "}
                    {(r.file_size / 1024 / 1024).toFixed(1)} MB &middot;{" "}
                    {r.download_count} 次下载
                    {r.version && <> &middot; v{r.version}</>}
                  </p>
                </div>
                <span className="rounded-lg bg-zinc-800 px-2.5 py-1 text-xs text-zinc-400">
                  {["游戏", "补丁", "语音", "攻略", "存档", "", "", "", "", "其他"][r.resource_type] || "其他"}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Public Saves */}
      {publicSaves.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-zinc-200">
            <svg className="h-5 w-5 text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
            </svg>
            玩家存档 ({publicSaves.length})
          </h2>
          <div className="space-y-2">
            {publicSaves.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-zinc-200">{s.title}</p>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {(s.file_size / 1024 / 1024).toFixed(2)} MB &middot;{" "}
                    {s.download_count} 次下载 &middot;{" "}
                    {new Date(s.published_at ?? s.created_at).toLocaleDateString("zh-CN")}
                  </p>
                  {s.description && (
                    <p className="mt-1 line-clamp-1 text-xs text-zinc-600">{s.description}</p>
                  )}
                </div>
                <button className="shrink-0 rounded-lg bg-emerald-600/20 px-3 py-1.5 text-xs font-medium text-emerald-400 transition hover:bg-emerald-600/30">
                  下载
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Comments */}
      <section className="mt-8 pb-12">
        <h2 className="mb-4 text-lg font-semibold text-zinc-200">
          评论 ({game.comment_count})
        </h2>

        {/* Comment form */}
        {isLoggedIn ? (
          <form onSubmit={handleComment} className="mb-6">
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="写下你的评论..."
              rows={3}
              className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition focus:border-violet-500"
            />
            <div className="mt-2 flex justify-end">
              <button
                type="submit"
                disabled={submitting || !commentText.trim()}
                className="rounded-xl bg-violet-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-violet-500 disabled:opacity-50"
              >
                {submitting ? "发送中..." : "发表评论"}
              </button>
            </div>
          </form>
        ) : (
          <p className="mb-6 text-sm text-zinc-500">
            <Link href="/login" className="text-violet-400 hover:underline">登录</Link>
            后发表评论
          </p>
        )}

        {/* Comment list */}
        <div className="space-y-4">
          {comments.length === 0 ? (
            <p className="py-8 text-center text-sm text-zinc-600">暂无评论，来做第一个评论的人吧</p>
          ) : (
            comments.map((c) => (
              <div key={c.id} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-800 text-xs font-medium text-zinc-400">
                    {(c.user?.username ?? "?")[0].toUpperCase()}
                  </div>
                  <span className="text-sm font-medium text-zinc-300">
                    {c.user?.username ?? "匿名"}
                  </span>
                  <span className="text-xs text-zinc-600">
                    {new Date(c.created_at).toLocaleDateString("zh-CN")}
                  </span>
                  <div className="flex-1" />
                  {isLoggedIn && (
                    <button
                      onClick={() => {
                        setReplyingTo(replyingTo === c.id ? null : c.id)
                        setReplyText("")
                      }}
                      className={`flex items-center gap-1 rounded-lg px-2 py-1 text-xs transition ${
                        replyingTo === c.id
                          ? "bg-violet-600/20 text-violet-300"
                          : "text-zinc-600 hover:bg-zinc-800 hover:text-zinc-300"
                      }`}
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
                      </svg>
                      回复
                    </button>
                  )}
                </div>
                <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                  {c.content}
                </p>

                {/* Replies */}
                {c.replies.length > 0 && (
                  <div className="mt-3 space-y-2 border-l-2 border-zinc-800 pl-4">
                    {c.replies.map((r) => (
                      <div key={r.id} className="group py-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-violet-400">
                            {r.user?.username ?? "匿名"}
                          </span>
                          <span className="text-xs text-zinc-600">
                            {new Date(r.created_at).toLocaleDateString("zh-CN")}
                          </span>
                          {isLoggedIn && (
                            <button
                              onClick={() => {
                                setReplyingTo(r.id)
                                setReplyText("")
                              }}
                              className="ml-auto hidden items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] text-zinc-600 transition hover:bg-zinc-800 hover:text-zinc-300 group-hover:flex"
                            >
                              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
                              </svg>
                              回复
                            </button>
                          )}
                        </div>
                        <p className="mt-1 text-sm text-zinc-400">{r.content}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Inline reply form */}
                {replyingTo !== null && (
                  (replyingTo === c.id || c.replies.some((r) => r.id === replyingTo)) && (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault()
                        // Always use top-level comment as parent_id (flat reply model)
                        const replyToUser = replyingTo === c.id
                          ? c.user?.username
                          : c.replies.find((r) => r.id === replyingTo)?.user?.username
                        handleReply(c.id, replyToUser ?? undefined)
                      }}
                      className="mt-3 flex gap-2 border-t border-zinc-800 pt-3"
                    >
                      <input
                        type="text"
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                        placeholder={
                          replyingTo === c.id
                            ? `回复 ${c.user?.username ?? "匿名"}...`
                            : `回复 ${c.replies.find((r) => r.id === replyingTo)?.user?.username ?? "匿名"}...`
                        }
                        className="flex-1 rounded-xl border border-zinc-800 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition focus:border-violet-500"
                        autoFocus
                      />
                      <button
                        type="submit"
                        disabled={replySubmitting || !replyText.trim()}
                        className="shrink-0 rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-violet-500 disabled:opacity-50"
                      >
                        {replySubmitting ? "..." : "发送"}
                      </button>
                      <button
                        type="button"
                        onClick={() => { setReplyingTo(null); setReplyText("") }}
                        className="shrink-0 rounded-xl px-3 py-2 text-sm text-zinc-500 transition hover:text-zinc-300"
                      >
                        取消
                      </button>
                    </form>
                  )
                )}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  )
}
