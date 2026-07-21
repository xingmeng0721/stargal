export interface TagOut {
  id: number
  name: string
  description: string | null
  usage_count: number
  category_name: string | null
  category_type: number | null
}

export interface TagCategoryOut {
  id: number
  name: string
  type: number
  sort_order: number
  tags: TagOut[]
}

export interface TagListResponse {
  items: TagOut[]
  total: number
}
