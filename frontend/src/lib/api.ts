export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  data: any;
  
  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

function extractErrorMessage(data: any, status: number): string {
  if (typeof data?.detail === 'string') return data.detail;
  if (typeof data?.detail?.message === 'string') return data.detail.message;
  if (Array.isArray(data?.detail) && data.detail.length > 0) {
    const first = data.detail[0];
    if (typeof first?.msg === 'string') return first.msg;
    if (typeof first?.message === 'string') return first.message;
    return JSON.stringify(data.detail);
  }
  if (typeof data?.message === 'string') return data.message;
  if (data && typeof data === 'object') {
    return data.error || data.message || JSON.stringify(data);
  }
  return `Request failed with status ${status}`;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      extractErrorMessage(data, response.status),
      data
    );
  }
  return response.json();
}

export const api = {
  get: async <T>(path: string): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    return handleResponse<T>(res);
  },
  
  post: async <T>(path: string, body: unknown): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(res);
  },
  
  patch: async <T>(path: string, body: unknown): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(res);
  },
  
  delete: async <T>(path: string): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    return handleResponse<T>(res);
  },
};
