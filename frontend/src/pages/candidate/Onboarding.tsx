import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileUp, Link2 } from "lucide-react";
import { api } from "../../api/client";
import type { CandidatePrefs, PersonRecord, ResumeUploadResult } from "../../types";
import { Button, Chip, ErrorState, Field, Panel, inputCls, cx } from "../../components/ui";
import { useSession } from "../../state/session";

const STEPS = ["Welcome", "Profile link", "Review", "Resume", "Preferences", "Finish"];
const val = (v: unknown) => (v == null || v === "" ? null : String(v));

export default function Onboarding() {
  const nav = useNavigate();
  const { setCandidateId } = useSession();
  const [step, setStep] = useState(0);
  const [url, setUrl] = useState("");
  const [person, setPerson] = useState<PersonRecord | null>(null);
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [resume, setResume] = useState<ResumeUploadResult | null>(null);
  const [prefs, setPrefs] = useState<CandidatePrefs>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<Error | null>(null);

  const run = async (fn: () => Promise<void>) => { setBusy(true); setErr(null); try { await fn(); } catch (e) { setErr(e as Error); } finally { setBusy(false); } };
  const next = () => setStep((s) => s + 1);

  const enrich = () => run(async () => { const p = await api.enrich(url.trim()); setPerson(p); setName(p.name ?? ""); next(); });
  const skipEnrich = () => { setPerson(null); next(); };
  const upload = () => run(async () => {
    const reg = await ensureRegistered();
    setResume(await api.uploadResume(reg.person_id, file!)); 
  });
  async function ensureRegistered(): Promise<PersonRecord> {
    const p = await api.register({ person_id: person?.person_id, name: name || person?.name || undefined, profile_url: person?.profile_url ?? (url || undefined), prefs: {} });
    setPerson(p); setCandidateId(p.person_id); return p;
  }
  const finish = () => run(async () => {
    const p = await api.register({ person_id: person?.person_id, name: name || person?.name || undefined, profile_url: person?.profile_url ?? (url || undefined), prefs: prefs as Record<string, unknown> });
    setCandidateId(p.person_id); nav("/candidate/profile");
  });

  return (
    <div className="pt-2">
      <p className="text-sm font-medium text-muted" aria-live="polite">Step {step + 1} of {STEPS.length} · {STEPS[step]}</p>
      <div className="mb-5 mt-2 flex gap-1" role="presentation">{STEPS.map((_, i) => <div key={i} className={cx("h-1.5 flex-1 rounded-full", i <= step ? "bg-brand" : "bg-line")} />)}</div>
      {err && <div className="mb-4"><ErrorState error={err} /></div>}

      {step === 0 && <Panel className="space-y-4 !p-5"><h1 className="text-2xl font-bold">Welcome to SwipeHire</h1><p className="text-muted">We'll pull what we can from your profile link, you correct anything wrong, add a resume and tell us what you want next. We never invent details.</p><Button size="lg" className="w-full" onClick={next}>Get started</Button></Panel>}

      {step === 1 && <Panel className="space-y-4 !p-5"><h1 className="text-xl font-bold">Your profile link</h1>
        <Field label="LinkedIn / profile URL" hint="Used only to look up public profile information. We don't log in or message anyone."><div className="relative"><Link2 size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden /><input className={cx(inputCls, "pl-11")} type="url" inputMode="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://linkedin.com/in/…" /></div></Field>
        <Button size="lg" className="w-full" disabled={busy || !/^https?:\/\//.test(url.trim())} onClick={enrich}>{busy ? "Looking up…" : "Look up my profile"}</Button>
        <Button variant="ghost" className="w-full" onClick={skipEnrich}>Skip — I'll enter details myself</Button></Panel>}

      {step === 2 && <Panel className="space-y-4 !p-5"><h1 className="text-xl font-bold">Review your profile</h1>
        <p className="text-sm text-muted">Imported from a public profile source — not independently verified. Correct anything that's wrong.</p>
        <Field label="Full name"><input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} /></Field>
        {person ? <dl className="space-y-2 text-sm">{([["Headline", person.headline], ["Current role", person.current_title && `${person.current_title}${person.current_company ? ` at ${person.current_company}` : ""}`], ["Location", person.location], ["Experience", person.experience_years != null ? `${person.experience_years} years` : null]] as const).map(([k, v]) => <div key={k} className="flex justify-between gap-4"><dt className="text-muted">{k}</dt><dd className="text-right">{val(v) ?? "Not available"}</dd></div>)}</dl> : <p className="text-sm text-muted">No profile data imported.</p>}
        {person && person.skills.length > 0 && <div className="flex flex-wrap gap-2">{person.skills.map((s) => <Chip key={s}>{s}</Chip>)}</div>}
        <Button size="lg" className="w-full" disabled={!name.trim()} onClick={next}>Looks right</Button></Panel>}

      {step === 3 && <Panel className="space-y-4 !p-5"><h1 className="text-xl font-bold">Upload your resume</h1>
        <label className="grid cursor-pointer place-items-center gap-2 rounded-2xl border-2 border-dashed border-line p-8 text-center focus-within:border-brand"><FileUp className="text-brand" aria-hidden />
          <span className="font-semibold">{file ? file.name : "Choose a PDF or DOCX"}</span><span className="text-xs text-muted">Max size is enforced by the server</span>
          <input type="file" className="sr-only" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setResume(null); }} /></label>
        {file && !resume && <Button size="lg" className="w-full" onClick={upload} disabled={busy}>{busy ? "Uploading…" : "Upload and parse"}</Button>}
        {resume && <div className="rounded-2xl bg-positive-soft p-4 text-sm"><p className="font-semibold text-positive">Resume received{resume.parser_status ? ` (${resume.parser_status})` : ""}</p>
          {resume.parsed_data ? <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(resume.parsed_data, null, 2)}</pre> : <p className="mt-1 text-muted">Nothing could be extracted automatically.</p>}</div>}
        <Button size="lg" variant={resume ? "primary" : "ghost"} className="w-full" onClick={next}>{resume ? "Continue" : "Skip for now"}</Button></Panel>}

      {step === 4 && <Panel className="space-y-4 !p-5"><h1 className="text-xl font-bold">What are you looking for?</h1>
        <Field label="Target role"><input className={inputCls} value={prefs.target_role ?? ""} onChange={(e) => setPrefs({ ...prefs, target_role: e.target.value })} /></Field>
        <Field label="Preferred locations" hint="Comma-separated"><input className={inputCls} value={(prefs.locations ?? []).join(", ")} onChange={(e) => setPrefs({ ...prefs, locations: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} /></Field>
        <Field label="Work mode"><select className={inputCls} value={prefs.work_mode ?? ""} onChange={(e) => setPrefs({ ...prefs, work_mode: e.target.value })}><option value="">Not specified</option><option>remote</option><option>hybrid</option><option>onsite</option></select></Field>
        <Field label="Availability / notice period"><input className={inputCls} value={prefs.availability ?? ""} onChange={(e) => setPrefs({ ...prefs, availability: e.target.value })} placeholder="e.g. 30 days" /></Field>
        <Field label="Salary expectation (optional)"><input className={inputCls} value={prefs.salary_expectation ?? ""} onChange={(e) => setPrefs({ ...prefs, salary_expectation: e.target.value })} /></Field>
        <Button size="lg" className="w-full" onClick={next}>Review</Button></Panel>}

      {step === 5 && <Panel className="space-y-4 !p-5"><h1 className="text-xl font-bold">All set?</h1>
        <dl className="space-y-2 text-sm"><div className="flex justify-between"><dt className="text-muted">Name</dt><dd>{name}</dd></div>
          {Object.entries(prefs).filter(([, v]) => v && (!Array.isArray(v) || v.length)).map(([k, v]) => <div key={k} className="flex justify-between gap-4"><dt className="text-muted">{k.replace(/_/g, " ")}</dt><dd className="text-right">{Array.isArray(v) ? v.join(", ") : String(v)}</dd></div>)}</dl>
        <p className="text-xs text-muted">Unfilled preferences stay "Unknown" — recruiters see only what you provide.</p>
        <Button size="lg" className="w-full" disabled={busy} onClick={finish}>{busy ? "Saving…" : "Complete profile"}</Button></Panel>}

      {step > 0 && <button className="mt-4 min-h-10 text-sm text-muted underline" onClick={() => setStep((s) => s - 1)}>Back</button>}
    </div>
  );
}
