import { Loader2, AlertTriangle, Inbox } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger"; size?: "md" | "lg" };
export function Button({ variant = "primary", size = "md", className, ...p }: BtnProps) {
  const v = {
    primary: "bg-brand text-white hover:bg-brand-dark",
    secondary: "bg-surface text-ink border border-line hover:bg-brand-soft",
    ghost: "text-ink hover:bg-brand-soft",
    danger: "bg-danger-soft text-danger hover:bg-danger hover:text-white",
  }[variant];
  return <button {...p} className={cx("inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-colors", size === "lg" ? "min-h-12 px-6 text-base" : "min-h-10 px-4 text-sm", v, className)} />;
}

export function Chip({ children, tone = "neutral", className }: { children: ReactNode; tone?: "neutral" | "brand" | "positive" | "adjacent" | "danger"; className?: string }) {
  const t = { neutral: "bg-bg text-ink border-line", brand: "bg-brand-soft text-brand border-transparent", positive: "bg-positive-soft text-positive border-transparent", adjacent: "bg-adjacent-soft text-[#5c6a1c] border-transparent", danger: "bg-danger-soft text-danger border-transparent" }[tone];
  return <span className={cx("inline-flex items-center gap-1 rounded-full border px-3 py-1 text-sm font-medium", t, className)}>{children}</span>;
}

export function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cx("rounded-3xl border border-line bg-surface p-6 shadow-[0_1px_2px_rgba(32,33,42,.04),0_8px_24px_rgba(32,33,42,.04)]", className)}>{children}</section>;
}

export function Avatar({ name, size = 56 }: { name?: string | null; size?: number }) {
  const initials = (name ?? "?").replace(/\(.*?\)/g, "").trim().split(/\s+/).slice(0, 2).map((s) => s[0]?.toUpperCase()).join("") || "?";
  return (
    <div aria-hidden className="grid shrink-0 place-items-center rounded-full bg-brand-soft font-bold text-brand" style={{ width: size, height: size, fontSize: size * 0.36 }}>{initials}</div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return <div role="status" className="flex items-center justify-center gap-3 p-12 text-muted"><Loader2 className="animate-spin" size={20} aria-hidden />{label}</div>;
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-2xl border border-danger/30 bg-danger-soft p-5 text-danger">
      <div className="flex items-center gap-2 font-semibold"><AlertTriangle size={18} aria-hidden /> Something went wrong</div>
      <p className="mt-1 text-sm">{error.message}</p>
      {onRetry && <Button variant="secondary" className="mt-3" onClick={onRetry}>Try again</Button>}
    </div>
  );
}

export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="grid place-items-center rounded-3xl border border-dashed border-line bg-surface/60 px-6 py-14 text-center">
      <Inbox className="text-muted" size={32} aria-hidden />
      <h3 className="mt-3 text-lg font-semibold">{title}</h3>
      {children && <p className="mt-1 max-w-md text-sm text-muted">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function PageHeader({ title, sub, action }: { title: string; sub?: string; action?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div><h1 className="text-2xl font-bold tracking-tight">{title}</h1>{sub && <p className="mt-1 text-muted">{sub}</p>}</div>
      {action}
    </header>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-muted">{hint}</span>}
    </label>
  );
}
export const inputCls = "min-h-12 w-full rounded-xl border border-line bg-surface px-4 text-base outline-none focus:border-brand focus:ring-4 focus:ring-brand-soft";

export function DemoBanner() {
  return <div className="bg-ink px-4 py-1.5 text-center text-xs font-medium text-white">Demo mode — all people and companies are fictional. Nothing is sent to anyone.</div>;
}

export function ListEditor({ label, values, onChange, placeholder, hint }: { label: string; values: string[]; onChange: (v: string[]) => void; placeholder?: string; hint?: string }) {
  return (
    <Field label={label} hint={hint ?? "Separate items with commas or new lines."}>
      <textarea
        className={cx(inputCls, "min-h-20 py-3")} placeholder={placeholder} defaultValue={values.join(", ")}
        onBlur={(e) => onChange(e.target.value.split(/[\n,]/).map((s) => s.trim()).filter(Boolean))}
      />
    </Field>
  );
}
