export interface UploadTaskOut {
  id: number
  upload_id: string
  user_id: number
  target_type: number // 0=game resource, 1=save
  game_id: number | null
  file_name: string
  file_size: number
  file_hash: string
  total_chunks: number
  uploaded_chunks: number
  status: number // 0=INIT, 1=UPLOADING, 2=MERGING, 3=COMPLETED, 4=FAILED
  created_at: string
}

export interface UploadInitCreate {
  target_type: number
  game_id?: number
  file_name: string
  file_size: number
  file_hash: string
  total_chunks: number
}

export interface ChunkUploadResponse {
  chunk_index: number
  chunk_hash: string | null
  message: string
}

export interface InstantUploadResponse {
  exists: boolean
  message: string
  resource_id: number | null
}

export const UPLOAD_STATUS_LABELS: Record<number, string> = {
  0: "初始化",
  1: "上传中",
  2: "合并中",
  3: "已完成",
  4: "失败",
}
