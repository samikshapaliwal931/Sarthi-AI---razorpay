/**
 * Typed API client with mock data support.
 *
 * To connect to real backend:
 * 1. Set VITE_API_BASE_URL in .env (e.g., http://localhost:8000/api/v1)
 * 2. Set VITE_USE_MOCK=false in .env
 * 3. Ensure backend is running with PostgreSQL and Redis
 *
 * Current mode: Mock data (for development without backend)
 */

export const API_BASE_URL = import.meta.env["VITE_API_BASE_URL"] ?? "http://localhost:8000/api/v1";
export const USE_MOCK = import.meta.env["VITE_USE_MOCK"] !== "false";

const LATENCY_MS = USE_MOCK ? 260 : 0;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status = 500) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Token management
let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem("sarthi_token", token);
  } else {
    localStorage.removeItem("sarthi_token");
  }
}

export function getAuthToken(): string | null {
  if (!authToken) {
    authToken = localStorage.getItem("sarthi_token");
  }
  return authToken;
}

export function clearAuth() {
  authToken = null;
  localStorage.removeItem("sarthi_token");
}

/**
 * Resolve a typed payload.
 * In mock mode: returns mock data with simulated latency
 * In real mode: makes actual HTTP request to backend
 */
export function request<T>(path: string, payload: T | (() => T)): Promise<T> {
  if (USE_MOCK) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        try {
          resolve(typeof payload === "function" ? (payload as () => T)() : payload);
        } catch (error) {
          reject(new ApiError(`Request to ${path} failed`, 500));
        }
      }, LATENCY_MS);
    });
  }

  // Real API call
  return (async () => {
    const token = getAuthToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new ApiError(error.detail || `HTTP ${response.status}`, response.status);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  })();
}

export function requestPost<T>(path: string, body: any): Promise<T> {
  if (USE_MOCK) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ success: true, ...body } as T);
      }, LATENCY_MS);
    });
  }

  return mutate<T>("POST", path, body);
}

export function requestPut<T>(path: string, body: any): Promise<T> {
  if (USE_MOCK) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ success: true, ...body } as T);
      }, LATENCY_MS);
    });
  }

  return mutate<T>("PUT", path, body);
}

export function requestPatch<T>(path: string, body: any): Promise<T> {
  if (USE_MOCK) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ success: true, ...body } as T);
      }, LATENCY_MS);
    });
  }

  return mutate<T>("PATCH", path, body);
}

export function requestDelete<T>(path: string, body?: any): Promise<T> {
  if (USE_MOCK) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ success: true } as T);
      }, LATENCY_MS);
    });
  }

  return mutate<T>("DELETE", path, body);
}

async function mutate<T>(
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  body?: any,
): Promise<T> {
  const token = getAuthToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(error.detail || `HTTP ${response.status}`, response.status);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return await response.json();
}

export function notFound(resource: string): never {
  throw new ApiError(`${resource} not found`, 404);
}
