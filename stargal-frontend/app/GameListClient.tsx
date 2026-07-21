"use client"

import { useCallback, useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { getGameList } from "@/lib/game"
import type { GameCard as GameCardType, GameSearchParams } from "@/types/game"
import GameCard from "@/components/GameCard"
import Pagination from "@/components/Pagination"

const SORT_OPTIONS = [
  { value: "latest", label: "最新发售" },
  { value: "rating", label: "评分最高" },
  { value: "views", label: "最多浏览" },
  { value: "downloads", label: "最多下载" },
]

const PAGE_SIZE = 24

export default function GameListClient() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [games, setGames] = useState<GameCardType[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  // Read filter state from URL
  const currentQ = searchParams.get("q") ?? ""
  const currentSort = searchParams.get("sort") ?? "latest"
  const currentPage = parseInt(searchParams.get("page") ?? "1", 10)
  const currentTag = searchParams.get("tag") ?? ""
  const currentNsfw = searchParams.get("nsfw")

  const fetchGames = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const params: GameSearchParams = {
        page: currentPage,
        page_size: PAGE_SIZE,
        sort: currentSort as GameSearchParams["sort"],
      }
      if (currentQ) params.q = currentQ
      if (currentTag) params.tag = currentTag
      if (currentNsfw !== null) params.nsfw = currentNsfw === "true"

      const data = await getGameList(params)
      setGames(data.items)
      setTotal(data.total)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "加载失败"
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [currentQ, currentSort, currentPage, currentTag, currentNsfw])

  useEffect(() => {
    fetchGames()
  }, [fetchGames])

  const updateParams = (updates: Record<string, string | undefined>) => {
    const params = new URLSearchParams(searchParams.toString())
    for (const [key, value] of Object.entries(updates)) {
      if (value === undefined || value === "") {
        params.delete(key)
      } else {
        params.set(key, value)
      }
    }
    if (!("page" in updates)) params.set("page", "1")
    router.push(`/?${params.toString()}`)
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      {/* Filter Bar */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        {/* Sort */}
        <div className="flex items-center gap-1 rounded-xl border border-zinc-800 bg-zinc-900 p-1">
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => updateParams({ sort: opt.value })}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                currentSort === opt.value
                  ? "bg-violet-600 text-white"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* NSFW toggle */}
        <button
          onClick={() => {
            const next = currentNsfw === "true" ? undefined : "true"
            updateParams({ nsfw: next })
          }}
          className={`rounded-xl border px-3 py-2 text-xs font-medium transition ${
            currentNsfw === "true"
              ? "border-red-800 bg-red-950 text-red-400"
              : "border-zinc-800 text-zinc-500 hover:text-zinc-300"
          }`}
        >
          {currentNsfw === "true" ? "R18 已开启" : "R18 过滤"}
        </button>

        {/* Active tag filter */}
        {currentTag && (
          <div className="flex items-center gap-1.5 rounded-xl border border-violet-800 bg-violet-950/50 px-3 py-2 text-xs text-violet-300">
            <span>标签: {currentTag}</span>
            <button
              onClick={() => updateParams({ tag: undefined })}
              className="ml-1 text-violet-400 hover:text-violet-200"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Search query indicator */}
        {currentQ && (
          <div className="flex items-center gap-1.5 rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-300">
            <span>搜索: {currentQ}</span>
            <button
              onClick={() => updateParams({ q: undefined })}
              className="ml-1 text-zinc-500 hover:text-zinc-300"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Result count */}
        {total > 0 && (
          <span className="ml-auto text-xs text-zinc-500">
            共 {total} 个游戏
          </span>
        )}
      </div>

      {/* Game Grid */}
      {loading ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {Array.from({ length: PAGE_SIZE }, (_, i) => (
            <div
              key={i}
              className="animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900"
            >
              <div className="aspect-[3/4] rounded-t-2xl bg-zinc-800" />
              <div className="space-y-2 p-3">
                <div className="h-4 w-3/4 rounded bg-zinc-800" />
                <div className="h-3 w-1/2 rounded bg-zinc-800" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-20">
          <svg className="mb-4 h-12 w-12 text-zinc-700" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <p className="text-sm text-zinc-400">{error}</p>
          <button
            onClick={fetchGames}
            className="mt-4 rounded-xl bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition hover:bg-zinc-700"
          >
            重试
          </button>
        </div>
      ) : games.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <svg className="mb-4 h-12 w-12 text-zinc-700" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <p className="text-sm text-zinc-400">没有找到匹配的游戏</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {games.map((game) => (
            <GameCard key={game.id} game={game} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && games.length > 0 && (
        <div className="mt-8">
          <Pagination
            current={currentPage}
            total={total}
            pageSize={PAGE_SIZE}
            onChange={(page) => updateParams({ page: String(page) })}
          />
        </div>
      )}
    </div>
  )
}
