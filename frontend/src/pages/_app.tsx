import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { SessionProvider } from "next-auth/react";
import { AuthTokenSync } from "@/components/AuthTokenSync";

export default function App({
  Component,
  pageProps: { session, ...pageProps },
}: AppProps) {
  return (
    <SessionProvider session={session}>
      <AuthTokenSync />
      <Component {...pageProps} />
    </SessionProvider>
  );
}
