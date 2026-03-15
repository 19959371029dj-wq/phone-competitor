const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function apiError(res: Response, json: Record<string, unknown>): string {
  const msg = (json.detail || json.message || res.statusText) as string;
  if (res.status === 404) {
    return "接口不存在(404)。请用「一键启动」或双击 start_backend.bat 启动手机竞品后端（不要运行 main.py），并确保端口为 8000。";
  }
  if (res.status >= 500) return `服务端错误(${res.status})，请稍后重试。`;
  return msg || "请求失败";
}

export async function api<T = unknown>(
  path: string,
  options?: RequestInit & { params?: Record<string, string> }
): Promise<{ success: boolean; data?: T; message?: string; [k: string]: unknown }> {
  let url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  if (options?.params) {
    const sp = new URLSearchParams(options.params);
    url += (url.includes("?") ? "&" : "?") + sp.toString();
    delete (options as Record<string, unknown>).params;
  }
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(apiError(res, json as Record<string, unknown>));
  return json;
}

export async function apiUpload<T = unknown>(
  path: string,
  file: File,
  body?: Record<string, unknown>
): Promise<{ success: boolean; data?: T; message?: string; [k: string]: unknown }> {
  const form = new FormData();
  form.append("file", file);
  if (body) {
    Object.entries(body).forEach(([k, v]) => form.append(k, String(v)));
  }
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  let res: Response;
  try {
    res = await fetch(url, { method: "POST", body: form });
  } catch (e) {
    throw new Error("无法连接后端，请确认已用 start.bat 或 start_backend.bat 启动后端（端口 8000）。");
  }
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(apiError(res, json as Record<string, unknown>));
  return json;
}
