/**
 * Typed HTTP error thrown when a backend API request returns a non-2xx status.
 */
class ApiError extends Error {
  /** HTTP status code returned by the server. */
  status: number;

  /** Creates an `ApiError` from an HTTP status code and server message. */
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/**
 * Typed `fetch` wrapper that sets JSON headers (unless sending `FormData`) and extracts FastAPI error details.
 */
export async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const headers: Record<string, string> = isFormData ? {} : { 'Content-Type': 'application/json' };

  const resp = await fetch(url, {
    ...init,
    headers: {
      ...headers,
      ...(init?.headers as Record<string, string> | undefined),
    },
  });

  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const errBody = await resp.json();
      if (errBody?.detail) detail = String(errBody.detail);
    } catch {
      // ignore non-JSON errors
    }
    throw new ApiError(resp.status, detail);
  }

  return (await resp.json()) as T;
}
