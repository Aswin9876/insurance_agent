// API client for the FastAPI backend
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await handle<{ access_token: string; user: { email: string; name: string } }>(res);
  localStorage.setItem("access_token", data.access_token);
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
}

export async function validateOnboarding(customer: Record<string, unknown>) {
  const res = await fetch(`${API_URL}/api/onboarding/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(customer),
  });
  return handle<{ valid: boolean; errors: string[] }>(res);
}

export async function runAgents(customer: Record<string, unknown>) {
  const res = await fetch(`${API_URL}/api/agents/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ customer }),
  });
  return handle<{ run_id: string; status: string; summary: import("./types").WorkflowSummary }>(res);
}

export async function sendChat(message: string, context: Record<string, unknown> = {}) {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, context }),
  });
  return handle<{ reply: string; guarded: boolean; source: string }>(res);
}

export interface Policy {
  product_id: string; name: string; category: string; premium: number;
  coverage: string; summary: string;
}

export async function fetchPolicies() {
  const res = await fetch(`${API_URL}/api/policies`);
  return handle<{ policies: Policy[] }>(res);
}