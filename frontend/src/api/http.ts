export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";
export const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {
  kind: "network" | "validation" | "unauthorized" | "not_found" | "server";
  status?: number;
  constructor(kind: ApiError["kind"], message: string, status?: number) {
    super(message);
    this.kind = kind;
    this.status = status;
  }
}

function detailText(d: unknown): string {
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => (x && typeof x === "object" && "msg" in x ? String((x as { msg: unknown }).msg) : String(x))).join("; ");
  return "Request failed";
}

export async function http<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    const isForm = init.body instanceof FormData;
    res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: isForm ? init.headers : { "Content-Type": "application/json", ...(init.headers ?? {}) },
    });
  } catch {
    throw new ApiError("network", `Cannot reach the SwipeHire backend at ${BASE_URL}. Is it running?`);
  }
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = detailText((await res.json()).detail); } catch { /* keep statusText */ }
    const kind = res.status === 401 || res.status === 403 ? "unauthorized" : res.status === 404 ? "not_found" : res.status < 500 ? "validation" : "server";
    throw new ApiError(kind, msg, res.status);
  }
  return (await res.json()) as T;
}

export const post = <T,>(path: string, body?: unknown) => http<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
