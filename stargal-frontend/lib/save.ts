import { apiFetch } from "./api"
import type { SaveOut, SaveListResponse, SaveCreate } from "@/types/save"

// ── My Saves ──────────────────────────────────────────────

export const getMySaves = (
  token: string,
  params?: { game_id?: number; visibility?: number; page?: number; page_size?: number }
) => {
  const qs = new URLSearchParams()
  if (params?.game_id) qs.set("game_id", String(params.game_id))
  if (params?.visibility !== undefined) qs.set("visibility", String(params.visibility))
  qs.set("page", String(params?.page ?? 1))
  qs.set("page_size", String(params?.page_size ?? 20))
  return apiFetch<SaveListResponse>(`/api/v1/users/me/saves?${qs}`, {}, token)
}

// ── Public Saves for a Game ───────────────────────────────

export const getGamePublicSaves = (gameId: number, page = 1, pageSize = 20) =>
  apiFetch<SaveListResponse>(
    `/api/v1/games/${gameId}/saves?page=${page}&page_size=${pageSize}`
  )

// ── Create Save ───────────────────────────────────────────

export const createSave = (data: SaveCreate, token: string) =>
  apiFetch<SaveOut>(
    "/api/v1/saves",
    { method: "POST", body: JSON.stringify(data) },
    token
  )

// ── Delete Save ───────────────────────────────────────────

export const deleteSave = (saveId: number, token: string) =>
  apiFetch<{ message: string }>(`/api/v1/saves/${saveId}`, { method: "DELETE" }, token)

// ── Publish Save ──────────────────────────────────────────

export const publishSave = (saveId: number, token: string) =>
  apiFetch<SaveOut>(`/api/v1/saves/${saveId}/publish`, { method: "POST" }, token)
