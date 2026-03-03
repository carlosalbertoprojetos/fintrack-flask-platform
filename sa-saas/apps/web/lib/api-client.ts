const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4000";

export class ApiError extends Error {
  public readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as { error?: string };
    return new ApiError(response.status, body.error ?? `API request failed: ${response.status}`);
  } catch {
    return new ApiError(response.status, `API request failed: ${response.status}`);
  }
}

async function request<TOutput>(path: string, init: RequestInit): Promise<TOutput> {
  const response = await fetch(`${API_URL}${path}`, init);

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as TOutput;
}

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  return request<T>(path, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    cache: "no-store"
  });
}

export async function apiPost<TInput, TOutput>(path: string, payload: TInput, token?: string): Promise<TOutput> {
  return request<TOutput>(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(payload)
  });
}

export async function apiPut<TInput, TOutput>(path: string, payload: TInput, token?: string): Promise<TOutput> {
  return request<TOutput>(path, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(payload)
  });
}
