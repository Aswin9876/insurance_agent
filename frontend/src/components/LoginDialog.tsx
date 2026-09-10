// Login modal using NextAuth credentials (validated against FastAPI)
import { useState } from "react";
import { signIn } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function LoginDialog() {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("demo@agent.ai");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    const res = await signIn("credentials", { email, password, redirect: false });
    setLoading(false);
    if (res?.error) setError("Invalid credentials. Try demo@agent.ai / demo1234");
    else setOpen(false);
  }

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)}>Sign in</Button>
      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
          >
            <motion.div
              className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl"
              initial={{ scale: 0.95, y: 8 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 8 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="mb-1 text-lg font-semibold">Sign in</h2>
              <p className="mb-4 text-sm text-slate-500">
                Demo account is pre-filled — just click sign in.
              </p>
              <form onSubmit={submit} className="space-y-3">
                <Input label="Email" type="email" value={email}
                  onChange={(e) => setEmail(e.target.value)} required />
                <Input label="Password" type="password" value={password}
                  onChange={(e) => setPassword(e.target.value)} required />
                {error && <p className="text-sm text-red-600">{error}</p>}
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Signing in…" : "Sign in"}
                </Button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}