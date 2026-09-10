// NextAuth credentials provider — validates against the FastAPI backend
// and stores the backend JWT for downstream agent calls.
import NextAuth, { type NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Demo Account",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "demo@agent.ai" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        try {
          const res = await fetch(`${API_URL}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials?.email,
              password: credentials?.password,
            }),
          });
          if (!res.ok) return null;
          const data = await res.json();
          // Keep backend JWT accessible to the client for agent runs
          return { id: data.user.email, name: data.user.name, email: data.user.email, backendToken: data.access_token } as never;
        } catch {
          return null;
        }
      },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        // expose backend token via token for the session callback
        (token as unknown as Record<string, unknown>).backendToken =
          (user as unknown as Record<string, unknown>).backendToken;
      }
      return token;
    },
    async session({ session, token }) {
      (session as unknown as Record<string, unknown>).backendToken =
        (token as unknown as Record<string, unknown>).backendToken;
      return session;
    },
  },
  pages: { signIn: "/" },
};

export default NextAuth(authOptions);