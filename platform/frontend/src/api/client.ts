// Single fetch wrapper — every page goes through here, never `fetch` directly.

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path: string, options?: RequestInit): Promise<Response> {
  const response = await fetch(`${BASE_URL}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${options?.method ?? "GET"} ${path} failed (${response.status}): ${body}`);
  }

  return response;
}

export const api = {
  get: async <T>(path: string) => (await request(path)).json() as Promise<T>,
  getText: async (path: string) => (await request(path)).text(),
  post: async <T>(path: string, body: unknown) =>
    (await request(path, { method: "POST", body: JSON.stringify(body) })).json() as Promise<T>,
};
