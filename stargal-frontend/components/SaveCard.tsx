"use client"

import { useState } from "react"
import type { SaveOut } from "@/types/save"
import { VISIBILITY_LABELS } from "@/types/save"

interface Props {
  save: SaveOut
  gameTitle?: string
  onPublish?: (id: number) => void
  onDelete?: (id: number) => void
  publishing?: boolean
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export default function SaveCard({ save, gameTitle, onPublish, onDelete, publishing }: Props) {
  const [confirmDelete, setConfirmDelete] = useState(false)

  return (
    <div className="group rounded-2xl border border-zinc-800 bg-zinc-900 p-4 transition hover:border-zinc-700">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-medium text-zinc-100">
            {save.title}
          </h3>
          {gameTitle && (
            <p className="mt-0.5 truncate text-xs text-zinc-500">{gameTitle}</p>
          )}
        </div>

        {/* Visibility badge */}
        <span
          className={`shrink-0 rounded-lg px-2 py-0.5 text-[11px] font-medium ${
            save.visibility === 1
              ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
              : "bg-zinc-800 text-zinc-400 border border-zinc-700"
          }`}
        >
          {VISIBILITY_LABELS[save.visibility] ?? "未知"}
        </span>
      </div>

      {/* Description */}
      {save.description && (
        <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-zinc-500">
          {save.description}
        </p>
      )}

      {/* Meta */}
      <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-zinc-600">
        <span className="flex items-center gap-1">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          {formatFileSize(save.file_size)}
        </span>
        {save.download_count > 0 && (
          <span className="flex items-center gap-1">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            {save.download_count}
          </span>
        )}
        <span>
          {new Date(save.created_at).toLocaleDateString("zh-CN")}
        </span>
      </div>

      {/* Actions */}
      <div className="mt-3 flex items-center gap-2 border-t border-zinc-800 pt-3">
        {save.visibility === 0 && onPublish && (
          <button
            onClick={() => onPublish(save.id)}
            disabled={publishing}
            className="rounded-lg bg-violet-600/20 px-3 py-1.5 text-xs font-medium text-violet-300 transition hover:bg-violet-600/30 disabled:opacity-50"
          >
            {publishing ? "发布中..." : "发布为公开"}
          </button>
        )}
        {save.visibility === 1 && (
          <span className="rounded-lg bg-emerald-950/50 px-3 py-1.5 text-xs text-emerald-400">
            已公开
          </span>
        )}
        <div className="flex-1" />
        {onDelete && (
          confirmDelete ? (
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-zinc-500">确认删除?</span>
              <button
                onClick={() => onDelete(save.id)}
                className="rounded-lg bg-red-600/20 px-2.5 py-1.5 text-xs font-medium text-red-400 transition hover:bg-red-600/30"
              >
                确认
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="rounded-lg px-2.5 py-1.5 text-xs text-zinc-500 transition hover:text-zinc-300"
              >
                取消
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="rounded-lg px-2.5 py-1.5 text-xs text-zinc-600 transition hover:bg-zinc-800 hover:text-red-400"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
            </button>
          )
        )}
      </div>
    </div>
  )
}
