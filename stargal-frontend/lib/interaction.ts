import { apiFetch } from "./api"
import type {
  CommentListResponse,
  CommentCreate,
  CommentOut,
  FavoriteListResponse,
  FavoriteOut,
  RatingOut,
  UserGameStatusOut,
} from "@/types/interaction"

// ── Comments ──────────────────────────────────────────────

export const getGameComments = (gameId: number, page = 1, pageSize = 20) =>
  apiFetch<CommentListResponse>(
    `/api/v1/games/${gameId}/comments?page=${page}&page_size=${pageSize}`
  )

export const postComment = (gameId: number, data: CommentCreate, token: string) =>
  apiFetch<CommentOut>(
    `/api/v1/games/${gameId}/comments`,
    { method: "POST", body: JSON.stringify(data) },
    token
  )

// ── Favorites ─────────────────────────────────────────────

export const getMyFavorites = (token: string, page = 1, pageSize = 20) =>
  apiFetch<FavoriteListResponse>(
    `/api/v1/users/me/favorites?page=${page}&page_size=${pageSize}`,
    {},
    token
  )

export const addFavorite = (gameId: number, token: string, folder?: string) =>
  apiFetch<FavoriteOut>(
    "/api/v1/favorites",
    { method: "POST", body: JSON.stringify({ game_id: gameId, folder }) },
    token
  )

export const removeFavorite = (gameId: number, token: string) =>
  apiFetch<{ message: string }>(`/api/v1/favorites/${gameId}`, { method: "DELETE" }, token)

// ── Likes ─────────────────────────────────────────────────

export const toggleLike = (targetType: number, targetId: number, token: string) =>
  apiFetch<{ liked: boolean }>(
    "/api/v1/likes/toggle",
    { method: "POST", body: JSON.stringify({ target_type: targetType, target_id: targetId }) },
    token
  )

// ── Rating ────────────────────────────────────────────────

export const rateGame = (gameId: number, score: number, token: string) =>
  apiFetch<RatingOut>(
    `/api/v1/games/${gameId}/rating`,
    { method: "POST", body: JSON.stringify({ score }) },
    token
  )

export const getMyRating = (gameId: number, token: string) =>
  apiFetch<RatingOut | null>(`/api/v1/games/${gameId}/rating/me`, {}, token)

// ── Play Status ───────────────────────────────────────────

export const setPlayStatus = (gameId: number, status: number, token: string) =>
  apiFetch<UserGameStatusOut>(
    `/api/v1/games/${gameId}/status`,
    { method: "POST", body: JSON.stringify({ status }) },
    token
  )

export const getPlayStatus = (gameId: number, token: string) =>
  apiFetch<UserGameStatusOut | null>(`/api/v1/games/${gameId}/status/me`, {}, token)
