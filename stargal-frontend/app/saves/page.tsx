"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { getMySaves, createSave, deleteSave, publishSave } from "@/lib/save"
import { getGameList } from "@/lib/game"
import { checkInstantUpload, initUpload, uploadChunk, mergeUpload } from "@/lib/upload"
import type { SaveOut } from "@/types/save"
import type { GameCard as GameCardType } from "@/types/game"
import SaveCard from "@/components/SaveCard"

const FILTERS = [
  { value: "all", label: "全部" },
  { value: "private", label: "私有", vis: 0 },
  { value: "public", label: "公开", vis: 1 },
]

const CHUNK_SIZE = 2 * 1024 * 1024 // 2MB per chunk

async function computeFileHash(file: File): Promise<string> {
  const buffer = await file.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("")
}

export default function SavesPage() {
  const router = useRouter()
  const { isLoggedIn, token } = useAuth()

  const [saves, setSaves] = useState<SaveOut[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState("all")
  const [publishingId, setPublishingId] = useState<number | null>(null)

  // Upload state
  const [showUpload, setShowUpload] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadTitle, setUploadTitle] = useState("")
  const [uploadDesc, setUploadDesc] = useState("")
  const [uploadGameId, setUploadGameId] = useState<number | null>(null)
  const [uploadGameQuery, setUploadGameQuery] = useState("")
  const [gameResults, setGameResults] = useState<GameCardType[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Game title cache
  const [gameTitles, setGameTitles] = useState<Record<number, string>>({})

  // Redirect if not logged in
  useEffect(() => {
    if (!isLoggedIn) {
      router.push("/login")
    }
  }, [isLoggedIn, router])

  // Fetch saves
  const fetchSaves = useCallback(async () => {
    if (!token) return
    setLoading(true)
    try {
      const params: { visibility?: number; page: number; page_size: number } = {
        page: 1,
        page_size: 50,
      }
      if (filter === "private") params.visibility = 0
      if (filter === "public") params.visibility = 1

      const data = await getMySaves(token, params)
      setSaves(data.items)
      setTotal(data.total)

      // Fetch game titles for the saves
      const gameIds = [...new Set(data.items.map((s) => s.game_id))]
      const newTitles: Record<number, string> = {}
      for (const gid of gameIds) {
        if (gameTitles[gid]) {
          newTitles[gid] = gameTitles[gid]
        } else {
          try {
            const list = await getGameList({ q: String(gid), page_size: 1 })
            if (list.items.length > 0 && list.items[0].id === gid) {
              newTitles[gid] = list.items[0].title
            } else {
              newTitles[gid] = `游戏 #${gid}`
            }
          } catch {
            newTitles[gid] = `游戏 #${gid}`
          }
        }
      }
      setGameTitles((prev) => ({ ...prev, ...newTitles }))
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [token, filter])

  useEffect(() => {
    if (token) fetchSaves()
  }, [fetchSaves, token])

  // Search games for upload
  useEffect(() => {
    if (!uploadGameQuery.trim()) {
      setGameResults([])
      return
    }
    const timer = setTimeout(async () => {
      try {
        const data = await getGameList({ q: uploadGameQuery, page_size: 5 })
        setGameResults(data.items)
      } catch {
        setGameResults([])
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [uploadGameQuery])

  // Actions
  const handlePublish = async (saveId: number) => {
    if (!token) return
    setPublishingId(saveId)
    try {
      await publishSave(saveId, token)
      setSaves((prev) =>
        prev.map((s) => (s.id === saveId ? { ...s, visibility: 1 } : s))
      )
    } catch {
      // ignore
    } finally {
      setPublishingId(null)
    }
  }

  const handleDelete = async (saveId: number) => {
    if (!token) return
    try {
      await deleteSave(saveId, token)
      setSaves((prev) => prev.filter((s) => s.id !== saveId))
      setTotal((prev) => prev - 1)
    } catch {
      // ignore
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    setUploadFile(file)
    if (file && !uploadTitle) {
      // Auto-fill title from filename (remove extension)
      setUploadTitle(file.name.replace(/\.[^.]+$/, ""))
    }
  }

  const handleUpload = async () => {
    if (!token || !uploadFile || !uploadGameId) return
    setUploading(true)

    try {
      // 1. Compute hash
      setUploadProgress("正在计算文件校验...")
      const fileHash = await computeFileHash(uploadFile)

      // 2. Check instant upload
      setUploadProgress("检查秒传...")
      const instant = await checkInstantUpload(fileHash, token)
      if (instant.exists) {
        setUploadProgress("秒传成功! 创建存档记录...")
      } else {
        // 3. Init upload
        setUploadProgress("初始化上传任务...")
        const totalChunks = Math.ceil(uploadFile.size / CHUNK_SIZE)
        const task = await initUpload(
          {
            target_type: 1, // GAME_SAVE
            game_id: uploadGameId,
            file_name: uploadFile.name,
            file_size: uploadFile.size,
            file_hash: fileHash,
            total_chunks: totalChunks,
          },
          token
        )

        // 4. Upload chunks
        for (let i = 0; i < totalChunks; i++) {
          setUploadProgress(`上传分块 ${i + 1}/${totalChunks}...`)
          const start = i * CHUNK_SIZE
          const end = Math.min(start + CHUNK_SIZE, uploadFile.size)
          const chunkBlob = uploadFile.slice(start, end)
          const chunkFile = new File([chunkBlob], `chunk_${i}`)
          await uploadChunk(task.upload_id, i, chunkFile, token)
        }

        // 5. Merge
        setUploadProgress("合并文件中...")
        await mergeUpload(task.upload_id, token)
      }

      // 6. Create save record
      setUploadProgress("创建存档记录...")
      const storagePath = `saves/${uploadGameId}/${Date.now()}_${uploadFile.name}`
      await createSave(
        {
          game_id: uploadGameId,
          title: uploadTitle || uploadFile.name,
          description: uploadDesc || undefined,
          storage_path: storagePath,
          file_size: uploadFile.size,
          file_hash: fileHash,
          visibility: 0, // private by default
        },
        token
      )

      // Done
      setShowUpload(false)
      setUploadFile(null)
      setUploadTitle("")
      setUploadDesc("")
      setUploadGameId(null)
      setUploadGameQuery("")
      fetchSaves()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "上传失败"
      setUploadProgress(`错误: ${message}`)
    } finally {
      setUploading(false)
    }
  }

  if (!isLoggedIn) return null

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">我的存档</h1>
          <p className="mt-1 text-sm text-zinc-500">
            管理你的私有云存档，可选择发布为公开分享
          </p>
        </div>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className={`flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-medium transition ${
            showUpload
              ? "border border-zinc-700 text-zinc-400 hover:text-white"
              : "bg-violet-600 text-white hover:bg-violet-500"
          }`}
        >
          {showUpload ? (
            "取消"
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              上传存档
            </>
          )}
        </button>
      </div>

      {/* Upload Form */}
      {showUpload && (
        <div className="mb-8 rounded-2xl border border-violet-800/50 bg-zinc-900 p-6">
          <h2 className="mb-4 text-lg font-semibold text-zinc-200">上传新存档</h2>

          <div className="space-y-4">
            {/* Game search */}
            <div>
              <label className="mb-1 block text-sm text-zinc-400">关联游戏 *</label>
              {uploadGameId ? (
                <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-800/50 px-4 py-2.5">
                  <span className="flex-1 text-sm text-zinc-200">
                    {gameResults.find((g) => g.id === uploadGameId)?.title ?? `游戏 #${uploadGameId}`}
                  </span>
                  <button
                    onClick={() => { setUploadGameId(null); setUploadGameQuery("") }}
                    className="text-xs text-zinc-500 hover:text-zinc-300"
                  >
                    更换
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <input
                    type="text"
                    placeholder="搜索游戏名称..."
                    value={uploadGameQuery}
                    onChange={(e) => setUploadGameQuery(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-800/50 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition focus:border-violet-500"
                  />
                  {gameResults.length > 0 && (
                    <div className="absolute left-0 right-0 top-full z-10 mt-1 rounded-xl border border-zinc-800 bg-zinc-900 py-1 shadow-xl">
                      {gameResults.map((g) => (
                        <button
                          key={g.id}
                          onClick={() => {
                            setUploadGameId(g.id)
                            setUploadGameQuery("")
                            setGameResults([])
                          }}
                          className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm text-zinc-300 hover:bg-zinc-800"
                        >
                          <span className="flex-1 truncate">{g.title}</span>
                          {g.developer && (
                            <span className="text-xs text-zinc-600">{g.developer}</span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* File */}
            <div>
              <label className="mb-1 block text-sm text-zinc-400">选择文件 *</label>
              <div
                onClick={() => fileInputRef.current?.click()}
                className="flex cursor-pointer items-center justify-center gap-3 rounded-xl border-2 border-dashed border-zinc-700 bg-zinc-800/30 px-4 py-6 transition hover:border-violet-600"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                {uploadFile ? (
                  <div className="text-center">
                    <p className="text-sm text-zinc-200">{uploadFile.name}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div className="text-center">
                    <svg className="mx-auto h-8 w-8 text-zinc-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
                    </svg>
                    <p className="mt-2 text-sm text-zinc-500">点击选择存档文件</p>
                  </div>
                )}
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="mb-1 block text-sm text-zinc-400">存档标题</label>
              <input
                type="text"
                placeholder="如: 真结局前存档 / 全线路收集"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                maxLength={100}
                className="w-full rounded-xl border border-zinc-800 bg-zinc-800/50 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition focus:border-violet-500"
              />
            </div>

            {/* Description */}
            <div>
              <label className="mb-1 block text-sm text-zinc-400">说明 (可选)</label>
              <textarea
                placeholder="描述一下这个存档..."
                value={uploadDesc}
                onChange={(e) => setUploadDesc(e.target.value)}
                rows={2}
                maxLength={500}
                className="w-full rounded-xl border border-zinc-800 bg-zinc-800/50 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition focus:border-violet-500"
              />
            </div>

            {/* Upload progress / button */}
            {uploading ? (
              <div className="flex items-center gap-3 rounded-xl bg-zinc-800/50 px-4 py-3">
                <svg className="h-4 w-4 animate-spin text-violet-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="text-sm text-zinc-300">{uploadProgress}</span>
              </div>
            ) : (
              <button
                onClick={handleUpload}
                disabled={!uploadFile || !uploadGameId}
                className="w-full rounded-xl bg-violet-600 py-3 text-sm font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                上传存档 (私有)
              </button>
            )}
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="mb-6 flex items-center gap-1 rounded-xl border border-zinc-800 bg-zinc-900 p-1 w-fit">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium transition ${
              filter === f.value
                ? "bg-violet-600 text-white"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            {f.label}
          </button>
        ))}
        {total > 0 && (
          <span className="ml-3 pr-2 text-xs text-zinc-500">共 {total} 个</span>
        )}
      </div>

      {/* Save list */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <div key={i} className="animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
              <div className="h-5 w-2/3 rounded bg-zinc-800" />
              <div className="mt-3 h-3 w-full rounded bg-zinc-800" />
              <div className="mt-4 h-8 w-full rounded bg-zinc-800" />
            </div>
          ))}
        </div>
      ) : saves.length === 0 ? (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 py-16 text-center">
          <svg className="mx-auto h-12 w-12 text-zinc-700" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.125l2.25 2.25m0 0l2.25 2.25M12 13.875l2.25-2.25M12 13.875l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
          </svg>
          <p className="mt-4 text-sm text-zinc-500">
            {filter === "all" ? "还没有存档" : filter === "private" ? "没有私有存档" : "没有公开存档"}
          </p>
          <button
            onClick={() => setShowUpload(true)}
            className="mt-3 text-sm text-violet-400 hover:underline"
          >
            上传你的第一个存档
          </button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {saves.map((save) => (
            <SaveCard
              key={save.id}
              save={save}
              gameTitle={gameTitles[save.game_id]}
              onPublish={handlePublish}
              onDelete={handleDelete}
              publishing={publishingId === save.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
