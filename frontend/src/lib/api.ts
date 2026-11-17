const API_BASE = 'http://localhost:8000/api/v1';

export async function fetchApi(path: string, options?: RequestInit) {
  const token = localStorage.getItem('wayline_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options?.headers || {}) },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData?.error?.message || `Request failed with status ${res.status}`);
  }

  return res.json();
}

