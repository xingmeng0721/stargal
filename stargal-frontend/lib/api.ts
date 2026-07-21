const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    // 401 → token 过期或无效，通知 AuthProvider 自动清除登录态
    if (res.status === 401 && token) {
      window.dispatchEvent(new CustomEvent("auth:expired"));
    }
    const data = await res.json().catch(() => ({}));
    throw new Error(data?.detail || "请求失败");
  }
  return res.json();
}