const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!

import type {
  UploadTaskOut,
  UploadInitCreate,
  ChunkUploadResponse,
  InstantUploadResponse,
} from "@/types/upload"

// ── Helper: JSON fetch with auth ──────────────────────────

async function uploadFetch<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    if (res.status === 401 && token) {
      window.dispatchEvent(new CustomEvent("auth:expired"))
    }
    const data = await res.json().catch(() => ({}))
    throw new Error(data?.detail || "请求失败")
  }
  return res.json()
}

// ── Instant Check ─────────────────────────────────────────

export const checkInstantUpload = (fileHash: string, token: string) =>
  uploadFetch<InstantUploadResponse>(
    `/api/v1/uploads/instant-check?file_hash=${fileHash}`,
    {},
    token
  )

// ── Init Upload ───────────────────────────────────────────

export const initUpload = (data: UploadInitCreate, token: string) =>
  uploadFetch<UploadTaskOut>(
    "/api/v1/uploads/init",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
    token
  )

// ── Upload Chunk ──────────────────────────────────────────

export const uploadChunk = (
  uploadId: string,
  chunkIndex: number,
  file: File,
  token: string,
  chunkHash?: string
) => {
  const formData = new FormData()
  formData.append("file", file)
  if (chunkHash) formData.append("chunk_hash", chunkHash)

  return uploadFetch<ChunkUploadResponse>(
    `/api/v1/uploads/${uploadId}/chunks/${chunkIndex}`,
    { method: "POST", body: formData },
    token
  )
}

// ── Get Upload Status ─────────────────────────────────────

export const getUploadStatus = (uploadId: string, token: string) =>
  uploadFetch<UploadTaskOut>(`/api/v1/uploads/${uploadId}`, {}, token)

// ── Get Uploaded Chunks (for resume) ──────────────────────

export const getUploadedChunks = (uploadId: string, token: string) =>
  uploadFetch<{ uploaded_chunks: number[] }>(`/api/v1/uploads/${uploadId}/chunks`, {}, token)

// ── Merge ─────────────────────────────────────────────────

export const mergeUpload = (uploadId: string, token: string) =>
  uploadFetch<UploadTaskOut>(`/api/v1/uploads/${uploadId}/merge`, { method: "POST" }, token)
