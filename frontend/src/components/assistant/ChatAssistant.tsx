// Floating AI assistant: insurance FAQs, policy explanations, onboarding
// help. Guardrails handled server-side (injection detection + PII masking).
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { sendChat } from "@/lib/api";
import { Button } from "@/components/ui/Button";

interface Msg {
  role: "user" | "bot";
  text: string;
  guarded?: boolean;
}

const SUGGESTIONS = [
  "What is the risk score?",
  "Tell me about Health Premium",
  "How does the match score work?",
  "Why do you need my consent?",
];

export function ChatAssistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([{
    role: "bot",
    text: "Hi! I'm your insurance assistant 🤖 — ask me about policies, risk scoring, coverage, or the onboarding steps.",
  }]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  async function send(text: string) {
    const msg = text.trim();
    if (!msg || busy) return;
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setInput("");
    setBusy(true);
    try {
      const res = await sendChat(msg);
      setMessages((m) => [...m, { role: "bot", text: res.reply, guarded: res.guarded }]);
    } catch {
      setMessages((m) => [...m, {
        role: "bot",
        text: "I'm having trouble reaching the server. Is the backend running on :8000?",
      }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {/* Floating button */}
      <motion.button
        className="fixed bottom-5 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-2xl text-white shadow-lg hover:bg-indigo-700"
        whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.95 }}
        onClick={() => setOpen((o) => !o)}
        aria-label="AI Assistant"
      >
        {open ? "✕" : "💬"}
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed bottom-24 right-5 z-50 flex h-[480px] w-[360px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl"
            initial={{ opacity: 0, y: 20, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.97 }}
          >
            <div className="border-b border-slate-100 bg-indigo-600 px-4 py-3 text-white">
              <p className="font-semibold">AI Insurance Assistant</p>
              <p className="text-xs opacity-80">Guardrails active · PII masked</p>
            </div>

            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {messages.map((m, i) => (
                <div key={i}
                  className={`max-w-[85%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap
                    ${m.role === "user"
                      ? "ml-auto bg-indigo-600 text-white"
                      : `bg-slate-100 text-slate-800 ${m.guarded ? "border border-red-300" : ""}`}`}>
                  {m.text}
                </div>
              ))}
              {busy && (
                <div className="w-16 rounded-xl bg-slate-100 px-3 py-2 text-sm">…</div>
              )}
              <div ref={endRef} />
            </div>

            {messages.length <= 1 && (
              <div className="flex flex-wrap gap-1.5 px-4 pb-2">
                {SUGGESTIONS.map((s) => (
                  <button key={s}
                    className="rounded-full border border-slate-200 px-2.5 py-1 text-[11px] text-slate-600 hover:border-indigo-400 hover:text-indigo-600"
                    onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            )}

            <form className="flex gap-2 border-t border-slate-100 p-3"
              onSubmit={(e) => { e.preventDefault(); send(input); }}>
              <input
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Ask about policies, risk…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <Button type="submit" size="sm" disabled={busy}>Send</Button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}