"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { getTagCategories } from "@/lib/tag"
import type { TagCategoryOut } from "@/types/tag"

const CATEGORY_ICONS: Record<number, string> = {
  0: "📖",  // 剧情/内容
  1: "✨",  // 萌点
  2: "🎮",  // 技术/制作
  3: "🏷️",  // 其它
}

const CATEGORY_COLORS: Record<number, string> = {
  0: "from-blue-500/20 to-blue-600/10 border-blue-800/50",
  1: "from-pink-500/20 to-pink-600/10 border-pink-800/50",
  2: "from-emerald-500/20 to-emerald-600/10 border-emerald-800/50",
  3: "from-zinc-500/20 to-zinc-600/10 border-zinc-700/50",
}

const TAG_HOVER_COLORS: Record<number, string> = {
  0: "hover:bg-blue-900/50 hover:text-blue-300 hover:border-blue-700",
  1: "hover:bg-pink-900/50 hover:text-pink-300 hover:border-pink-700",
  2: "hover:bg-emerald-900/50 hover:text-emerald-300 hover:border-emerald-700",
  3: "hover:bg-zinc-800 hover:text-zinc-200 hover:border-zinc-600",
}

export default function TagsPage() {
  const [categories, setCategories] = useState<TagCategoryOut[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getTagCategories()
      .then(setCategories)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="animate-pulse space-y-8">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-3">
              <div className="h-6 w-32 rounded bg-zinc-800" />
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: 8 }, (_, j) => (
                  <div key={j} className="h-8 w-20 rounded-lg bg-zinc-800" />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-zinc-100">标签浏览</h1>
      <p className="mb-8 text-sm text-zinc-500">
        通过标签发现你感兴趣的 Galgame 类型和主题
      </p>

      {categories.length === 0 ? (
        <p className="py-12 text-center text-zinc-500">暂无标签数据</p>
      ) : (
        <div className="space-y-8">
          {categories.map((cat) => (
            <section key={cat.id}>
              <div className="mb-3 flex items-center gap-2">
                <span className="text-lg">
                  {CATEGORY_ICONS[cat.type] ?? "🏷️"}
                </span>
                <h2 className="text-lg font-semibold text-zinc-200">
                  {cat.name}
                </h2>
                <span className="text-xs text-zinc-600">
                  ({cat.tags.length})
                </span>
              </div>

              <div
                className={`rounded-2xl border bg-gradient-to-br p-4 ${
                  CATEGORY_COLORS[cat.type] ?? CATEGORY_COLORS[3]
                }`}
              >
                <div className="flex flex-wrap gap-2">
                  {cat.tags.map((tag) => (
                    <Link
                      key={tag.id}
                      href={`/?tag=${encodeURIComponent(tag.name)}`}
                      className={`rounded-xl border border-zinc-700/50 bg-zinc-900/60 px-3 py-1.5 text-sm text-zinc-300 transition ${
                        TAG_HOVER_COLORS[cat.type] ?? TAG_HOVER_COLORS[3]
                      }`}
                    >
                      {tag.name}
                      {tag.usage_count > 0 && (
                        <span className="ml-1.5 text-xs text-zinc-600">
                          {tag.usage_count}
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
