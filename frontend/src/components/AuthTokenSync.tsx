// Bridges NextAuth session → localStorage so the FastAPI client
// (api.ts authHeaders) always has the backend JWT to send to /api/agents/run.
import { useEffect } from "react";
import { useSession } from "next-auth/react";

export function AuthTokenSync() {
  const { data: session } = useSession();

  useEffect(() => {
    const token = (session as unknown as Record<string, unknown> | null)
      ?.backendToken;
    if (typeof token === "string" && token) {
      localStorage.setItem("access_token", token);
    } else if (!session) {
      // signed out — clear the stored backend token
      localStorage.removeItem("access_token");
    }
  }, [session]);

  return null;
}