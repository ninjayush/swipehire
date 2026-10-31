import { AnimatePresence, motion, useMotionValue, useReducedMotion, useTransform } from "framer-motion";
import { Bookmark, Heart, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { DeckCard, RecruiterAction } from "../types";
import { CandidateCard } from "./CandidateCard";
import { cx } from "./ui";

const THRESHOLD = 140;

interface Props {
  cards: DeckCard[];
  onAction: (card: DeckCard, action: RecruiterAction) => Promise<void> | void;
  onDone: React.ReactNode;
}

export function SwipeDeck({ cards, onAction, onDone }: Props) {
  const [index, setIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [exit, setExit] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const reduce = useReducedMotion();
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-300, 300], [-8, 8]);
  const likeOp = useTransform(x, [20, THRESHOLD], [0, 1]);
  const passOp = useTransform(x, [-THRESHOLD, -20], [1, 0]);
  const scroller = useRef<HTMLDivElement>(null);
  const card = cards[index];

  const act = useCallback(async (action: RecruiterAction) => {
    if (!card || busy) return;
    setBusy(true); setErr(null);
    try {
      await onAction(card, action);
      setExit(action === "shortlist" ? { x: 600, y: 0 } : action === "pass" ? { x: -600, y: 0 } : { x: 0, y: 500 });
      setIndex((i) => i + 1);
      x.set(0);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Action failed");
      x.set(0);
    } finally { setBusy(false); }
  }, [card, busy, onAction, x]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (t.closest("input,textarea,select")) return;
      if (e.key === "ArrowLeft") { e.preventDefault(); void act("pass"); }
      else if (e.key === "ArrowRight") { e.preventDefault(); void act("shortlist"); }
      else if (e.key === "ArrowDown" || e.key.toLowerCase() === "s") { if (e.key === "ArrowDown") e.preventDefault(); void act("save"); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [act]);

  useEffect(() => { scroller.current?.scrollTo({ top: 0 }); }, [index]);

  if (!card) return <div className="mx-auto max-w-xl">{onDone}</div>;
  const isMember = card.person.membership_status === "registered";

  return (
    <div className="mx-auto flex w-full max-w-xl flex-col gap-4">
      <div className="flex items-center justify-between text-sm text-muted" aria-live="polite">
        <span>{index} of {cards.length} reviewed</span>
        <div className="h-1.5 w-40 rounded-full bg-line"><div className="h-1.5 rounded-full bg-brand transition-all" style={{ width: `${(index / cards.length) * 100}%` }} /></div>
      </div>

      <div className="relative h-[calc(100dvh-20rem)] min-h-[420px]">
        {cards[index + 1] && <div aria-hidden className="absolute inset-x-4 top-3 bottom-0 rounded-[28px] border border-line bg-surface/70" />}
        <AnimatePresence mode="popLayout">
          <motion.div
            key={card.person.person_id}
            className="absolute inset-0 overflow-hidden rounded-[28px] border border-line bg-surface shadow-[0_2px_4px_rgba(32,33,42,.05),0_16px_40px_rgba(32,33,42,.08)]"
            style={{ x, rotate: reduce ? 0 : rotate, touchAction: "pan-y" }}
            drag={busy ? false : "x"} dragSnapToOrigin dragElastic={0.6}
            onDragEnd={(_, info) => {
              if (info.offset.x > THRESHOLD) void act("shortlist");
              else if (info.offset.x < -THRESHOLD) void act("pass");
            }}
            initial={reduce ? false : { scale: 0.96, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            exit={reduce ? { opacity: 0 } : { ...exit, opacity: 0, transition: { duration: 0.25 } }}
          >
            <motion.div aria-hidden style={{ opacity: likeOp }} className="pointer-events-none absolute left-6 top-6 z-10 rounded-xl border-2 border-positive bg-surface px-3 py-1 font-bold text-positive">{isMember ? "INTEREST" : "SHORTLIST"}</motion.div>
            <motion.div aria-hidden style={{ opacity: passOp }} className="pointer-events-none absolute right-6 top-6 z-10 rounded-xl border-2 border-danger bg-surface px-3 py-1 font-bold text-danger">PASS</motion.div>
            <div ref={scroller} className="h-full overflow-y-auto overscroll-contain" tabIndex={0} aria-label="Candidate details, scrollable">
              <CandidateCard card={card} />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {err && <div role="alert" className="rounded-xl bg-danger-soft p-3 text-sm text-danger">{err}</div>}

      <div className="flex items-center justify-center gap-4" role="group" aria-label="Candidate actions">
        <Dock label="Pass" hint="←" onClick={() => act("pass")} disabled={busy} tone="danger"><X size={26} /></Dock>
        <Dock label="Save for later" hint="↓" onClick={() => act("save")} disabled={busy} tone="neutral"><Bookmark size={24} /></Dock>
        <Dock label={isMember ? "Express interest" : "Shortlist (internal)"} hint="→" onClick={() => act("shortlist")} disabled={busy} tone="brand" big><Heart size={28} /></Dock>
      </div>
      <p className="text-center text-xs text-muted">
        {isMember ? "Interest sends an in-app request the candidate can accept or decline." : "Not on platform: shortlisting is internal only — no notification is sent."}
        {" "}Keys: ← pass · → shortlist · ↓ save
      </p>
    </div>
  );
}

function Dock({ label, hint, tone, big, children, ...p }: { label: string; hint: string; tone: "danger" | "neutral" | "brand"; big?: boolean } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const t = { danger: "bg-danger-soft text-danger", neutral: "bg-surface text-ink border border-line", brand: "bg-brand text-white" }[tone];
  return (
    <div className="flex flex-col items-center gap-1">
      <button {...p} aria-label={`${label} (${hint})`} className={cx("grid place-items-center rounded-full shadow-sm transition-transform hover:scale-105 active:scale-95", big ? "h-16 w-16" : "h-14 w-14", t)}>{children}</button>
      <span className="text-xs font-medium text-muted">{label}</span>
    </div>
  );
}
