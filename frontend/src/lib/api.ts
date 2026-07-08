// Client API verso il backend FastAPI. La base URL viene dall'env pubblico
// (in dev: http://localhost:8000). La ANTHROPIC_API_KEY NON è mai qui: sta solo lato server.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getJSON(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

export function getSession() {
  return getJSON("/api/session");
}

export function getSetupParams(car?: string, track?: string) {
  const q = new URLSearchParams();
  if (car) q.set("car", car);
  if (track) q.set("track", track);
  return getJSON(`/api/setup-params?${q.toString()}`);
}

export async function postAnalysis(prompt: string) {
  const res = await fetch(`${API_BASE}/api/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error(`POST /api/analysis → ${res.status}`);
  return res.json() as Promise<{ question: string; text: string; source: string }>;
}
