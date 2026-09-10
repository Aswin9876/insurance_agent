// App header with login state
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/router";
import { logout } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { LoginDialog } from "@/components/LoginDialog";

export function Header() {
  const { data: session } = useSession();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <button
          className="flex items-center gap-2 font-semibold"
          onClick={() => router.push("/")}
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-sm text-white">AI</span>
          <span>InsureAgent</span>
          <span className="hidden text-xs font-normal text-slate-400 sm:inline">
            Multi-Agent Onboarding Platform
          </span>
        </button>
        {session ? (
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-600 sm:inline">
              {session.user?.name || session.user?.email}
            </span>
            <Button size="sm" variant="outline" onClick={() => { logout(); signOut({ callbackUrl: "/" }); }}>
              Sign out
            </Button>
          </div>
        ) : (
          <LoginDialog />
        )}
      </div>
    </header>
  );
}