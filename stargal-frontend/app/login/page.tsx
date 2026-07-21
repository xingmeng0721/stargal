"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { loginApi } from "@/lib/auth"
import { useAuth } from "@/lib/auth-context"

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [msg, setMsg] = useState("")
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMsg("")
    setLoading(true)
    try {
      const res = await loginApi({ username, password })
      login(res.access_token)
      router.push("/")
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "登录失败"
      setMsg(message)
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
          <h1 className="text-2xl font-bold text-zinc-100">欢迎回来</h1>
          <p className="mt-1 text-sm text-zinc-500">登录你的 StarGal 账号</p>
        </div>

        <div className="space-y-3">
          <div>
            <label className="mb-1.5 block text-sm text-zinc-400">用户名</label>
            <input
              className="w-full rounded-xl border border-zinc-700 bg-zinc-800 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
              placeholder="输入用户名"
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
              placeholder="输入密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </div>

        {msg && (
          <p className="rounded-lg bg-red-950/50 px-3 py-2 text-sm text-red-400">
            {msg}
          </p>
        )}

        <button
          disabled={loading}
          className="w-full rounded-xl bg-violet-600 py-2.5 text-sm font-medium text-white transition hover:bg-violet-500 disabled:opacity-50"
        >
          {loading ? "登录中..." : "登录"}
        </button>

        <p className="text-center text-sm text-zinc-500">
          没有账号？{" "}
          <Link href="/register" className="text-violet-400 hover:underline">
            立即注册
          </Link>
        </p>
      </form>
    </div>
  )
}
