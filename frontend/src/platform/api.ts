const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export type RequestOptions = {
  token?: string | null;
};

function headersFor(options: RequestOptions = {}, contentType?: string) {
  const headers: Record<string, string> = {
    Accept: "application/json"
  };
  if (contentType) {
    headers["Content-Type"] = contentType;
  }
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  return headers;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(
      payload.message ?? "API request failed.",
      payload.code ?? "HTTP_ERROR",
      response.status,
      payload.details ?? {}
    );
  }
  return response.json() as Promise<T>;
}

export async function apiGet<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: headersFor(options)
  });
  return parseResponse<T>(response);
}

export async function apiPost<T>(
  path: string,
  body: Record<string, unknown>,
  options: RequestOptions = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: headersFor(options, "application/json"),
    body: JSON.stringify(body)
  });
  return parseResponse<T>(response);
}

export async function apiPut<T>(
  path: string,
  body: Record<string, unknown>,
  options: RequestOptions = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: headersFor(options, "application/json"),
    body: JSON.stringify(body)
  });
  return parseResponse<T>(response);
}
