import type { AnalysisResponse, ApiErrorBody, HealthResponse } from "./types";

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").trim();

// Empty base => relative URLs, served by the Vite dev proxy. Production builds
// must set VITE_API_BASE_URL; otherwise the app reports a configuration error.
export const API_BASE_URL = RAW_BASE.replace(/\/+$/, "");
export const API_CONFIGURED = API_BASE_URL !== "" || import.meta.env.DEV;

export const TICKER_PATTERN = /^[A-Z0-9][A-Z0-9.-]{0,9}$/;

// Must exceed the backend's worst case (three Groq calls with SDK retries).
const ANALYZE_TIMEOUT_MS = 180_000;
const HEALTH_TIMEOUT_MS = 60_000; // Render free instances can take ~1 min to wake.

export class ApiRequestError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.status = status;
    this.body = body;
  }
}

function url(path: string) {
  return `${API_BASE_URL}${path}`;
}

async function request<T>(path: string, init: RequestInit, timeoutMs: number, signal?: AbortSignal): Promise<T> {
  if (!API_CONFIGURED) {
    throw new ApiRequestError(0, {
      code: "frontend_misconfigured",
      message: "VITE_API_BASE_URL is not set for this deployment, so the backend cannot be reached.",
    });
  }

  const timeout = AbortSignal.timeout(timeoutMs);
  const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;

  let res: Response;
  try {
    res = await fetch(url(path), { ...init, signal: combined });
  } catch (err) {
    if (signal?.aborted) throw err;
    if (timeout.aborted) {
      throw new ApiRequestError(0, {
        code: "timeout",
        message: "The request timed out before the council returned a result.",
      });
    }
    throw new ApiRequestError(0, {
      code: "network_error",
      message: "Could not reach the analysis backend. It may be offline or waking up.",
    });
  }

  let payload: unknown = null;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }

  if (!res.ok) {
    const body =
      payload && typeof payload === "object" && "error" in payload
        ? (payload as { error: ApiErrorBody }).error
        : { code: `http_${res.status}`, message: `The backend responded with HTTP ${res.status}.` };
    throw new ApiRequestError(res.status, body);
  }

  if (payload === null) {
    throw new ApiRequestError(res.status, {
      code: "invalid_response",
      message: "The backend returned a response that could not be parsed.",
    });
  }
  return payload as T;
}

export function fetchHealth(signal?: AbortSignal) {
  return request<HealthResponse>("/health", { method: "GET" }, HEALTH_TIMEOUT_MS, signal);
}

export function analyzeTicker(ticker: string, signal?: AbortSignal) {
  return request<AnalysisResponse>(
    "/api/analyze",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    },
    ANALYZE_TIMEOUT_MS,
    signal,
  );
}
