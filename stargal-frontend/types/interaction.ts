import type { GameCard } from "./game"

export interface CommentUser {
  id: number
  username: string
  avatar_url: string | null
}

export interface CommentOut {
  id: number
  user: CommentUser | null
  game_id: number
  parent_id: number | null
  content: string
  like_count: number
  reply_count: number
  replies: CommentOut[]
  created_at: string
}

export interface CommentListResponse {
  items: CommentOut[]
  total: number
  page: number
  page_size: number
}

export interface CommentCreate {
  content: string
  parent_id?: number
}

export interface FavoriteOut {
  id: number
  game: GameCard | null
  folder: string | null
  created_at: string
}

export interface FavoriteListResponse {
  items: FavoriteOut[]
  total: number
  page: number
  page_size: number
}

export interface RatingOut {
  id: number
  user_id: number
  game_id: number
  score: number
  created_at: string
}

export interface UserGameStatusOut {
  id: number
  user_id: number
  game_id: number
  status: number
  total_minutes: number
  last_played_at: string | null
  created_at: string
}

export const PLAY_STATUS_LABELS: Record<number, string> = {
  0: "想玩",
  1: "在玩",
  2: "已完",
  3: "搁置",
  4: "弃坑",
}
