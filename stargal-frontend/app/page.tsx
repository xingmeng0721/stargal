import { Suspense } from "react"
import GameListClient from "./GameListClient"

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-7xl px-4 py-6">
          <div className="mb-6 flex items-center gap-3">
            <div className="h-9 w-64 animate-pulse rounded-xl bg-zinc-800" />
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {Array.from({ length: 24 }, (_, i) => (
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
        </div>
      }
    >
      <GameListClient />
    </Suspense>
  )
}
