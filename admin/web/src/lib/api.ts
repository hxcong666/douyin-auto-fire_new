// 后端接口调用。会话令牌在 HttpOnly Cookie 中由浏览器自动携带，JS 无法读取；
// 修改类请求额外带上 CSRF 令牌。

import type { FriendsConfig, LogResponse, Me, SaveResponse, StatusResponse } from "./types";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

let csrfToken = "";

type ErrorBody = { detail?: string | { msg: string; loc: (string | number)[] }[] };

function describe(body: ErrorBody, fallback: string): string {
  const { detail } = body;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]) {
    const first = detail[0];
    return `${first.loc.slice(1).join(".")}: ${first.msg}`;
  }
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  if (init.method && init.method !== "GET") headers.set("X-CSRF-Token", csrfToken);
  const response = await fetch(path, { ...init, headers, credentials: "same-origin", cache: "no-store" });
  if (response.status === 204) return undefined as T;
  const body: unknown = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, describe(body as ErrorBody, `请求失败 (${response.status})`));
  return body as T;
}

function remember(me: Me): Me {
  csrfToken = me.csrf_token;
  return me;
}

export const api = {
  me: () => request<Me>("/api/auth/me").then(remember),
  login: (username: string, password: string) =>
    request<Me>("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }).then(remember),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  getConfig: () => request<FriendsConfig>("/api/config"),
  saveConfig: (config: FriendsConfig) =>
    request<SaveResponse>("/api/config", { method: "PUT", body: JSON.stringify(config) }),
  status: () => request<StatusResponse>("/api/status"),
  log: (date: string) => request<LogResponse>(`/api/logs/${encodeURIComponent(date)}`),
};
