import { apiFetch } from "./api";
import type { UserCreate, UserLogin, Token } from "@/types/auth";

export const registerApi = (data: UserCreate) =>
  apiFetch("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) });

export const loginApi = (data: UserLogin) =>
  apiFetch<Token>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(data) });

export const logoutApi = (token: string) =>
  apiFetch<{ message: string }>("/api/v1/auth/logout", { method: "POST" }, token);