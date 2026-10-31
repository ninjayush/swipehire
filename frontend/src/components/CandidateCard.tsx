import { BadgeCheck, Briefcase, GraduationCap, HelpCircle, MapPin, Sparkles, UserX } from "lucide-react";
import type { DeckCard, Rec } from "../types";
import { Avatar, Chip, cx } from "./ui";

const s = (v: unknown) => (typeof v === "string" || typeof v === "number" ? String(v) : "");
const LABELS: Record<string, string> = { skills: "Skills", experience: "Experience", role_domain: "Role & domain", seniority: "Seniority", contextual: "Context" };

export function FitBadge({ type }: { type?: "direct" | "adjacent" | null }) {
  if (!type) return null;
  return type === "direct"
    ? <Chip tone="positive"><BadgeCheck size={14} aria-hidden /> Direct fit</Chip>
    : <Chip tone="adjacent"><Sparkles size={14} aria-hidden /> Adjacent fit</Chip>;
}

export function MembershipBadge({ registered }: { registered: boolean }) {
  return registered
    ? <Chip tone="brand">On SwipeHire</Chip>
    : <Chip tone="neutral"><UserX size={14} aria-hidden /> Not on platform</Chip>;
}

function Unknown({ label }: { label: string }) {
  return <span className="inline-flex items-center gap-1 text-sm text-muted"><HelpCircle size={14} aria-hidden /> {label}: Unknown — needs confirmation</span>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="border-t border-line pt-5"><h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">{title}</h3>{children}</section>;
}

export function CandidateCard({ card, expanded = true }: { card: DeckCard; expanded?: boolean }) {
  const { person: p, evaluation: e } = card;
  const registered = p.membership_status === "registered";
  const score = e.fit_score != null ? Math.round(e.fit_score) : null;
  return (
    <article className="flex flex-col gap-5 p-6 sm:p-8" aria-label={`Candidate ${p.name ?? "Unnamed"}`}>
      <div className="flex items-start gap-4">
        <Avatar name={p.name} size={64} />
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-tight">{p.name ?? "Name unavailable"}</h2>
          <p className="text-base text-ink/80">{p.headline ?? p.current_title ?? <Unknown label="Headline" />}</p>
        </div>
        <div className="text-right" aria-label={score != null ? `Fit score ${score} out of 100` : "Fit score unavailable"}>
          <div className="text-3xl font-bold text-brand">{score ?? "—"}</div>
          <div className="text-xs text-muted">fit / 100</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2"><FitBadge type={e.fit_type} /><MembershipBadge registered={registered} /></div>

      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <div className="flex items-center gap-2"><Briefcase size={16} className="text-muted" aria-hidden />
          <dt className="sr-only">Current role</dt>
          <dd>{p.current_title ? `${p.current_title}${p.current_company ? ` · ${p.current_company}` : ""}` : <Unknown label="Current role" />}</dd></div>
        <div className="flex items-center gap-2"><MapPin size={16} className="text-muted" aria-hidden />
          <dt className="sr-only">Location</dt><dd>{p.location ?? <Unknown label="Location" />}</dd></div>
        <div className="flex items-center gap-2"><GraduationCap size={16} className="text-muted" aria-hidden />
          <dt className="sr-only">Experience</dt><dd>{p.experience_years != null ? `${p.experience_years} years experience` : <Unknown label="Experience" />}</dd></div>
      </dl>

      {p.skills.length > 0 && <div className="flex flex-wrap gap-2">{p.skills.slice(0, 5).map((k) => <Chip key={k} tone="neutral">{k}</Chip>)}</div>}

      <div className="rounded-2xl bg-brand-soft p-4">
        <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand">Why this candidate</div>
        <p className="text-[15px] leading-relaxed">{e.match_explanation ?? "No explanation provided by the matching service."}</p>
      </div>

      {expanded && (
        <>
          {p.resume_highlights.length > 0 && (
            <Section title="About their work">
              <div className="grid gap-3">{p.resume_highlights.map((h: Rec, i) => (
                <div key={i} className="rounded-2xl border border-line p-4">
                  <div className="text-sm font-semibold text-brand">{s(h.label) || "Highlight"}</div>
                  <p className="mt-1">{s(h.text) || s(h.summary) || s(h.description)}</p>
                </div>))}</div>
            </Section>
          )}

          <Section title="Career timeline">
            {p.employment_history.length === 0 ? <Unknown label="Work history" /> : (
              <ol className="space-y-4 border-l-2 border-line pl-4">{p.employment_history.map((j: Rec, i) => (
                <li key={i}><div className="font-semibold">{s(j.title) || s(j.job_title) || "Role"}{s(j.company) && ` · ${s(j.company)}`}</div>
                  <div className="text-sm text-muted">{[s(j.start), s(j.end)].filter(Boolean).join(" – ")}</div>
                  {s(j.summary) && <p className="mt-1 text-sm">{s(j.summary)}</p>}</li>))}</ol>)}
            {!registered && <p className="mt-3 text-xs text-muted">Imported from a public profile source; not independently verified employment history.</p>}
          </Section>

          <Section title="Education">
            {p.education.length === 0 ? <Unknown label="Education" /> : <ul className="space-y-1">{p.education.map((ed: Rec, i) => (
              <li key={i}>{[s(ed.degree), s(ed.school)].filter(Boolean).join(" — ")}{s(ed.year) && <span className="text-muted"> ({s(ed.year)})</span>}</li>))}</ul>}
          </Section>

          {registered && (
            <Section title="What they're looking for next">
              {Object.keys(p.candidate_preferences).length === 0 ? <Unknown label="Preferences" /> : (
                <ul className="space-y-1 text-sm">{Object.entries(p.candidate_preferences).map(([k, v]) => <li key={k}><span className="text-muted">{k.replace(/_/g, " ")}:</span> {Array.isArray(v) ? v.join(", ") : s(v)}</li>)}</ul>)}
            </Section>
          )}

          <Section title="Fit breakdown">
            {Object.keys(e.component_scores).length === 0 ? <Unknown label="Score breakdown" /> : (
              <ul className="space-y-2">{Object.entries(e.component_scores).map(([k, v]) => (
                <li key={k} className="text-sm"><div className="flex justify-between"><span>{LABELS[k] ?? k}</span><span className="font-semibold">{Math.round(v)}</span></div>
                  <div className="mt-1 h-2 rounded-full bg-bg" role="presentation"><div className={cx("h-2 rounded-full", e.fit_type === "adjacent" ? "bg-adjacent" : "bg-brand")} style={{ width: `${Math.max(0, Math.min(100, v))}%` }} /></div></li>))}</ul>)}
            {e.evidence_coverage != null && <p className="mt-3 text-sm text-muted">Evidence coverage: {Math.round(e.evidence_coverage * 100)}% of criteria supported by profile data.</p>}
          </Section>

          {e.reasons.length > 0 && <Section title="Reasons shown"><ul className="list-disc space-y-1 pl-5 text-sm">{e.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul></Section>}

          {(e.evidence?.length ?? 0) > 0 && <Section title="Evidence"><ul className="space-y-2 text-sm">{e.evidence!.map((ev, i) => <li key={i}><span className="font-semibold">{ev.criterion}:</span> {ev.evidence_text} {ev.source_type && <span className="text-muted">({ev.source_type.replace(/_/g, " ")})</span>}</li>)}</ul></Section>}

          {p.source_metadata.length > 0 && <Section title="Sources"><ul className="text-xs text-muted">{p.source_metadata.map((m: Rec, i) => <li key={i}>{s(m.source) || "source"}{s(m.note) && ` — ${s(m.note)}`}</li>)}</ul></Section>}
        </>
      )}
    </article>
  );
}
