import { apiFetch } from "./api"
import type { TagCategoryOut, TagListResponse } from "@/types/tag"

export const getTagCategories = () =>
  apiFetch<TagCategoryOut[]>("/api/v1/tags/categories")

export const getTagList = (categoryId?: number) =>
  apiFetch<TagListResponse>(
    categoryId ? `/api/v1/tags?category_id=${categoryId}` : "/api/v1/tags"
  )
