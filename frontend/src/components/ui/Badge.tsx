const styles: Record<string, string> = {
  low: "bg-emerald-100 text-emerald-700",
  medium: "bg-amber-100 text-amber-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
  success: "bg-emerald-100 text-emerald-700",
  fallback: "bg-amber-100 text-amber-700",
  blocked: "bg-red-100 text-red-700",
  neutral: "bg-slate-100 text-slate-600",
  info: "bg-indigo-100 text-indigo-700",
};

export function Badge({ tone = "neutral", children }: { tone?: string; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[tone] || styles.neutral}`}>
      {children}
    </span>
  );
}