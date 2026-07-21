"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { logoutApi } from "@/lib/auth"
import { getMyFavorites } from "@/lib/interaction"
import { getMySaves } from "@/lib/save"
import type { FavoriteOut } from "@/types/interaction"
import type { SaveOut } from "@/types/save"
import { PLAY_STATUS_LABELS } from "@/types/interaction"
import GameCard from "@/components/GameCard"

export default function DashboardPage() {
  const router = useRouter()
  const { isLoggedIn, token, logout } = useAuth()
  const [favorites, setFavorites] = useState<FavoriteOut[]>([])
  const [saves, setSaves] = useState<SaveOut[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoggedIn) {
      router.push("/login")
      return
    }
    if (token) {
      Promise.all([
        getMyFavorites(token).then((data) => data.items).catch(() => [] as FavoriteOut[]),
        getMySaves(token).then((data) => data.items).catch(() => [] as SaveOut[]),
      ])
        .then(([favItems, saveItems]) => {
          setFavorites(favItems)
          setSaves(saveItems)
        })
        .finally(() => setLoading(false))
    }
  }, [isLoggedIn, token, router])

  const handleLogout = async () => {
    try {
      if (token) await logoutApi(token)
    } catch {
      // ignore
    } finally {
      logout()
      router.push("/")
    }
  }

  if (!isLoggedIn) return null

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">个人中心</h1>
          <p className="mt-1 text-sm text-zinc-500">管理你的收藏和游玩状态</p>
        </div>
        <button
          onClick={handleLogout}
          className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-400 transition hover:border-red-800 hover:text-red-400"
        >
          退出登录
        </button>
      </div>

      {/* Quick Stats */}
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs text-zinc-500">收藏</p>
          <p className="mt-1 text-2xl font-bold text-zinc-200">
            {favorites.length}
          </p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs text-zinc-500">存档</p>
          <p className="mt-1 text-2xl font-bold text-zinc-200">
            {saves.length}
          </p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs text-zinc-500">公开存档</p>
          <p className="mt-1 text-2xl font-bold text-zinc-200">
            {saves.filter((s) => s.visibility === 1).length}
          </p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs text-zinc-500">存档下载</p>
          <p className="mt-1 text-2xl font-bold text-zinc-200">
            {saves.reduce((sum, s) => sum + s.download_count, 0)}
          </p>
        </div>
      </div>

      {/* Favorites */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-zinc-200">我的收藏</h2>
        {loading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {Array.from({ length: 6 }, (_, i) => (
              <div key={i} className="animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900">
                <div className="aspect-[3/4] rounded-t-2xl bg-zinc-800" />
                <div className="space-y-2 p-3">
                  <div className="h-4 w-3/4 rounded bg-zinc-800" />
                </div>
              </div>
            ))}
          </div>
        ) : favorites.length === 0 ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900 py-12 text-center">
            <p className="text-sm text-zinc-500">还没有收藏任何游戏</p>
            <Link href="/" className="mt-2 inline-block text-sm text-violet-400 hover:underline">
              去发现游戏
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {favorites.map((f) =>
              f.game ? <GameCard key={f.id} game={f.game} /> : null
            )}
          </div>
        )}
      </section>

      {/* Saves */}
      <section className="mt-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-200">我的存档</h2>
          <Link
            href="/saves"
            className="text-sm text-violet-400 hover:underline"
          >
            管理全部
          </Link>
        </div>
        {loading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }, (_, i) => (
              <div key={i} className="animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
                <div className="h-4 w-2/3 rounded bg-zinc-800" />
                <div className="mt-3 h-3 w-full rounded bg-zinc-800" />
              </div>
            ))}
          </div>
        ) : saves.length === 0 ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900 py-8 text-center">
            <p className="text-sm text-zinc-500">还没有上传存档</p>
            <Link href="/saves" className="mt-2 inline-block text-sm text-violet-400 hover:underline">
              去上传存档
            </Link>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {saves.slice(0, 6).map((s) => (
              <div key={s.id} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="truncate text-sm font-medium text-zinc-200">{s.title}</h3>
                  <span className={`shrink-0 rounded-md px-1.5 py-0.5 text-[10px] ${
                    s.visibility === 1
                      ? "bg-emerald-950 text-emerald-400"
                      : "bg-zinc-800 text-zinc-500"
                  }`}>
                    {s.visibility === 1 ? "公开" : "私有"}
                  </span>
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  {(s.file_size / 1024 / 1024).toFixed(1)} MB &middot;{" "}
                  {new Date(s.created_at).toLocaleDateString("zh-CN")}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
