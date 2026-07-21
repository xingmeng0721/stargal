export interface TagBrief {
  id: number
  name: string
}

export interface GameCard {
  id: number
  title: string
  original_title: string | null
  cover_url: string | null
  developer: string | null
  release_date: string | null
  nsfw: boolean
  bgm_score: number | null
  vndb_score: number | null
  rating_avg: number
  rating_count: number
  view_count: number
  favorite_count: number
  download_count: number
  comment_count: number
  tags: TagBrief[]
}

export interface GameListResponse {
  items: GameCard[]
  total: number
  page: number
  page_size: number
}

export interface GameAlias {
  id: number
  alias: string
  lang: string | null
}

export interface GameImage {
  id: number
  url: string
  sort_order: number
}

export interface GameResource {
  id: number
  resource_type: number
  title: string
  file_name: string
  file_size: number
  download_count: number
  version: string | null
  created_at: string
}

export interface GameDetail {
  id: number
  title: string
  original_title: string | null
  description: string | null
  description_zh: string | null
  description_en: string | null
  description_ja: string | null
  cover_url: string | null
  nsfw: boolean
  developer: string | null
  publisher: string | null
  release_date: string | null
  bgm_id: number | null
  bgm_score: number | null
  bgm_rank: number | null
  vndb_id: string | null
  vndb_score: number | null
  rating_avg: number
  rating_count: number
  view_count: number
  favorite_count: number
  download_count: number
  comment_count: number
  is_favorited: boolean
  status: number
  aliases: GameAlias[]
  images: GameImage[]
  tags: TagBrief[]
  resources: GameResource[]
  created_at: string
  updated_at: string
}

export interface GameSearchParams {
  q?: string
  tag?: string
  developer?: string
  nsfw?: boolean
  year?: number
  sort?: "latest" | "rating" | "views" | "downloads"
  page?: number
  page_size?: number
}
