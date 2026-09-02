const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface RequestOptions extends RequestInit {
  orgId?: string;
  token?: string;
}

export class ApiError extends Error {
  errorCode: string;
  status: number;
  meta?: Record<string, any>;

  constructor(message: string, status: number, errorCode: string = "API_ERROR", meta?: Record<string, any>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errorCode = errorCode;
    this.meta = meta;
  }
}

export async function fetchApi<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { orgId, token, headers: customHeaders, ...restOptions } = options;

  let authToken = token;
  if (!authToken && typeof window !== "undefined") {
    authToken = localStorage.getItem("pravah_access_token") || undefined;
  }

  let activeOrgId = orgId;
  if (!activeOrgId && typeof window !== "undefined") {
    activeOrgId = localStorage.getItem("pravah_active_org_id") || undefined;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(customHeaders as Record<string, string>),
  };

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  if (activeOrgId) {
    headers["X-Organisation-Id"] = activeOrgId;
  }

  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const response = await fetch(url, {
    ...restOptions,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    let errorCode = "HTTP_ERROR";
    let meta = undefined;

    try {
      const errJson = await response.json();
      errorDetail = errJson.message || errJson.detail || errorDetail;
      errorCode = errJson.error_code || errorCode;
      meta = errJson.meta;
    } catch {
      // response wasn't JSON
    }

    throw new ApiError(errorDetail, response.status, errorCode, meta);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
