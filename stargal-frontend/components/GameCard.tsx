import Link from "next/link"
import type { GameCard as GameCardType } from "@/types/game"
import StarRating from "./StarRating"

interface Props {
  game: GameCardType
}

export default function GameCard({ game }: Props) {
  const score = game.bgm_score ?? game.rating_avg
  const topTags = game.tags.slice(0, 3)

  return (
    <Link href={`/game/${game.id}`} className="group block">
      <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 transition-all duration-300 hover:border-zinc-700 hover:shadow-lg hover:shadow-violet-500/5">
        {/* Cover Image */}
        <div className="relative aspect-[3/4] overflow-hidden bg-zinc-800">
          {game.cover_url ? (
            <img
              src={game.cover_url}
              alt={game.title}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              <svg className="h-12 w-12 text-zinc-700" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
              </svg>
            </div>
          )}
          {/* NSFW badge */}
          {game.nsfw && (
            <span className="absolute left-2 top-2 rounded-md bg-red-600/90 px-2 py-0.5 text-[10px] font-bold text-white backdrop-blur-sm">
              R18
            </span>
          )}
          {/* Score badge */}
          {score > 0 && (
            <span className="absolute right-2 top-2 rounded-lg bg-black/70 px-2 py-1 text-xs font-bold text-amber-400 backdrop-blur-sm">
              {Number(score).toFixed(1)}
            </span>
          )}
        </div>

        {/* Info */}
        <div className="p-3">
          <h3 className="line-clamp-2 text-sm font-medium leading-snug text-zinc-100 transition group-hover:text-violet-300">
            {game.title}
          </h3>

          {game.original_title && game.original_title !== game.title && (
            <p className="mt-0.5 line-clamp-1 text-xs text-zinc-500">
              {game.original_title}
            </p>
          )}

          {/* Developer */}
          {game.developer && (
            <p className="mt-1.5 text-xs text-zinc-400">{game.developer}</p>
          )}

          {/* Stars */}
          <div className="mt-2 flex items-center gap-1.5">
            <StarRating value={Number(score)} size="sm" readonly />
            {game.rating_count > 0 && (
              <span className="text-[11px] text-zinc-500">
                ({game.rating_count})
              </span>
            )}
          </div>

          {/* Tags */}
          {topTags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {topTags.map((tag) => (
                <span
                  key={tag.id}
                  className="rounded-md bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400"
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}

          {/* Stats bar */}
          <div className="mt-2 flex items-center gap-3 text-[11px] text-zinc-600">
            {game.view_count > 0 && (
              <span className="flex items-center gap-0.5">
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {game.view_count}
              </span>
            )}
            {game.favorite_count > 0 && (
              <span className="flex items-center gap-0.5">
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                </svg>
                {game.favorite_count}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}
