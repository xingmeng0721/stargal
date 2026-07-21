"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { registerApi } from "@/lib/auth"

export default function RegisterPage() {
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPw, setConfirmPw] = useState("")
  const [msg, setMsg] = useState("")
  const [msgType, setMsgType] = useState<"error" | "success">("error")
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMsg("")

    if (password !== confirmPw) {
      setMsg("两次输入的密码不一致")
      setMsgType("error")
      return
    }

    setLoading(true)
    try {
      await registerApi({ username, password })
      setMsg("注册成功，正在跳转登录页...")
      setMsgType("success")
      setTimeout(() => router.push("/login"), 800)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "注册失败"
      setMsg(message)
      setMsgType("error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm space-y-5 rounded-2xl border border-zinc-800 bg-zinc-900 p-8"
      >
        <div className="text-center">
          <h1 className="text-2xl font-bold text-zinc-100">加入 StarGal</h1>
          <p className="mt-1 text-sm text-zinc-500">创建你的 Galgame 社区账号</p>
        </div>

        <div className="space-y-3">
          <div>
            <label className="mb-1.5 block text-sm text-zinc-400">用户名</label>
            <input
              className="w-full rounded-xl border border-zinc-700 bg-zinc-800 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
              placeholder="3-50 个字符"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm text-zinc-400">密码</label>
            <input
              className="w-full rounded-xl border border-zinc-700 bg-zinc-800 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
              type="password"
              placeholder="至少 6 个字符"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm text-zinc-400">确认密码</label>
            <input
              className="w-full rounded-xl border border-zinc-700 bg-zinc-800 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
              type="password"
              placeholder="再次输入密码"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
            />
          </div>
        </div>

        {msg && (
          <p
            className={`rounded-lg px-3 py-2 text-sm ${
              msgType === "success"
                ? "bg-emerald-950/50 text-emerald-400"
                : "bg-red-950/50 text-red-400"
            }`}
          >
            {msg}
          </p>
        )}

        <button
          disabled={loading}
          className="w-full rounded-xl bg-violet-600 py-2.5 text-sm font-medium text-white transition hover:bg-violet-500 disabled:opacity-50"
        >
          {loading ? "注册中..." : "注册"}
        </button>

        <p className="text-center text-sm text-zinc-500">
          已有账号？{" "}
          <Link href="/login" className="text-violet-400 hover:underline">
            立即登录
          </Link>
        </p>
      </form>
    </div>
  )
}
