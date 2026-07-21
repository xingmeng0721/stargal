import { apiFetch } from "./api"
import type { GameListResponse, GameDetail, GameSearchParams } from "@/types/game"

function buildQueryString(params: GameSearchParams): string {
  const qs = new URLSearchParams()
  if (params.q) qs.set("q", params.q)
  if (params.tag) qs.set("tag", params.tag)
  if (params.developer) qs.set("developer", params.developer)
  if (params.nsfw !== undefined) qs.set("nsfw", String(params.nsfw))
  if (params.year) qs.set("year", String(params.year))
  if (params.sort) qs.set("sort", params.sort)
  if (params.page) qs.set("page", String(params.page))
  if (params.page_size) qs.set("page_size", String(params.page_size))
  const str = qs.toString()
  return str ? `?${str}` : ""
}

export const getGameList = (params: GameSearchParams = {}) =>
  apiFetch<GameListResponse>(`/api/v1/games${buildQueryString(params)}`)

export const getGameDetail = (id: number, token?: string) =>
  apiFetch<GameDetail>(`/api/v1/games/${id}`, {}, token)
