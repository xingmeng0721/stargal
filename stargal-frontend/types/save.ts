export interface SaveOut {
  id: number
  game_id: number
  user_id: number
  title: string
  description: string | null
  storage_path: string
  file_size: number
  file_hash: string | null
  visibility: number // 0=private, 1=public
  published_at: string | null
  download_count: number
  created_at: string
  updated_at: string
}

export interface SaveListResponse {
  items: SaveOut[]
  total: number
  page: number
  page_size: number
}

export interface SaveCreate {
  game_id: number
  title: string
  description?: string
  storage_path: string
  file_size: number
  file_hash?: string
  visibility?: number // 0=private (default), 1=public
}

export const VISIBILITY_LABELS: Record<number, string> = {
  0: "私有",
  1: "公开",
}
