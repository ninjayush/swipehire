import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import type { JobRequirements } from "../../types";
import { normalizeRequirements } from "../../api/mapping";
import { Button, ErrorState, Field, ListEditor, PageHeader, Panel, inputCls, cx } from "../../components/ui";
import { useSession } from "../../state/session";

export default function NewJob() {
  const { company } = useSession();
  const nav = useNavigate();
  const [mode, setMode] = useState<"jd" | "structured">("jd");
  const [jd, setJd] = useState("");
  const [req, setReq] = useState<JobRequirements>(normalizeRequirements({}));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<Error | null>(null);
  const set = <K extends keyof JobRequirements>(k: K, v: JobRequirements[K]) => setReq((r) => ({ ...r, [k]: v }));

  if (!company) return <Panel>Confirm your company first. <Link className="font-semibold text-brand" to="/recruiter/company">Set up company</Link></Panel>;
  const valid = mode === "jd" ? jd.trim().length > 20 : req.title.trim().length > 0 && req.must_have_skills.length > 0;

  async function submit() {
    setBusy(true); setErr(null);
    try {
      const job = await api.createJob(company!.id, mode === "jd" ? { raw_jd: jd } : { requirements: req });
      nav(`/recruiter/jobs/${job.job_id}/requirements`);
    } catch (e) { setErr(e as Error); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Create job" sub="Paste a job description or enter requirements yourself. You'll confirm everything before discovery." />
      <div role="tablist" aria-label="Input method" className="mb-4 inline-flex rounded-2xl border border-line bg-surface p-1">
        {(["jd", "structured"] as const).map((m) => (
          <button key={m} role="tab" aria-selected={mode === m} onClick={() => setMode(m)} className={cx("rounded-xl px-4 py-2 text-sm font-semibold", mode === m ? "bg-brand text-white" : "text-ink/70")}>{m === "jd" ? "Paste a job description" : "Build with fields"}</button>))}
      </div>
      <Panel>
        {mode === "jd" ? (
          <Field label="Job description" hint="Parsed on the server; you can edit the result on the next screen."><textarea className={cx(inputCls, "min-h-72 py-3")} value={jd} onChange={(e) => setJd(e.target.value)} placeholder="Paste the full job description here…" /></Field>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Job title"><input className={inputCls} value={req.title} onChange={(e) => set("title", e.target.value)} /></Field>
            <Field label="Seniority"><input className={inputCls} value={req.seniority ?? ""} onChange={(e) => set("seniority", e.target.value || null)} placeholder="Senior" /></Field>
            <Field label="Min years experience"><input type="number" min={0} className={inputCls} value={req.min_experience_years ?? ""} onChange={(e) => set("min_experience_years", e.target.value === "" ? null : Number(e.target.value))} /></Field>
            <Field label="Max years experience"><input type="number" min={0} className={inputCls} value={req.max_experience_years ?? ""} onChange={(e) => set("max_experience_years", e.target.value === "" ? null : Number(e.target.value))} /></Field>
            <ListEditor label="Must-have skills" values={req.must_have_skills} onChange={(v) => set("must_have_skills", v)} placeholder="Python, SQL" hint="Mandatory — candidates missing these are excluded." />
            <ListEditor label="Preferred skills" values={req.preferred_skills} onChange={(v) => set("preferred_skills", v)} hint="Nice to have — soft preference only." />
            <ListEditor label="Mandatory qualifications" values={req.mandatory_qualifications} onChange={(v) => set("mandatory_qualifications", v)} />
            <ListEditor label="Preferred qualifications" values={req.preferred_qualifications} onChange={(v) => set("preferred_qualifications", v)} />
            <ListEditor label="Locations" values={req.locations} onChange={(v) => set("locations", v)} />
            <ListEditor label="Work modes" values={req.work_modes} onChange={(v) => set("work_modes", v)} placeholder="remote, hybrid, onsite" />
            <ListEditor label="Dealbreakers" values={req.dealbreakers} onChange={(v) => set("dealbreakers", v)} />
            <ListEditor label="Required candidate fields" values={req.required_fields} onChange={(v) => set("required_fields", v)} placeholder="availability, resume" hint="Candidates missing these are excluded." />
          </div>)}
        {err && <div className="mt-4"><ErrorState error={err} /></div>}
        <div className="mt-6"><Button size="lg" onClick={submit} disabled={!valid || busy}>{busy ? "Creating…" : mode === "jd" ? "Parse and review" : "Continue to review"}</Button></div>
      </Panel>
    </>
  );
}
