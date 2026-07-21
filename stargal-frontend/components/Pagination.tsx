"use client"

interface Props {
  current: number
  total: number
  pageSize: number
  onChange: (page: number) => void
}

export default function Pagination({ current, total, pageSize, onChange }: Props) {
  const totalPages = Math.ceil(total / pageSize)
  if (totalPages <= 1) return null

  const getPageNumbers = (): (number | "...")[] => {
    const pages: (number | "...")[] = []
    const delta = 2

    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
      return pages
    }

    pages.push(1)
    if (current > delta + 2) pages.push("...")

    const start = Math.max(2, current - delta)
    const end = Math.min(totalPages - 1, current + delta)
    for (let i = start; i <= end; i++) pages.push(i)

    if (current < totalPages - delta - 1) pages.push("...")
    pages.push(totalPages)

    return pages
  }

  return (
    <div className="flex items-center justify-center gap-1.5">
      <button
        onClick={() => onChange(current - 1)}
        disabled={current <= 1}
        className="rounded-lg border border-zinc-800 px-3 py-2 text-sm text-zinc-400 transition hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
      </button>

      {getPageNumbers().map((page, i) =>
        page === "..." ? (
          <span key={`dots-${i}`} className="px-2 text-zinc-600">
            ...
          </span>
        ) : (
          <button
            key={page}
            onClick={() => onChange(page)}
            className={`min-w-[36px] rounded-lg px-3 py-2 text-sm transition ${
              page === current
                ? "bg-violet-600 font-medium text-white"
                : "border border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-white"
            }`}
          >
            {page}
          </button>
        )
      )}

      <button
        onClick={() => onChange(current + 1)}
        disabled={current >= totalPages}
        className="rounded-lg border border-zinc-800 px-3 py-2 text-sm text-zinc-400 transition hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      </button>
    </div>
  )
}
