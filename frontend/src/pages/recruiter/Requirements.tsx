import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertCircle, ShieldAlert } from "lucide-react";
import { api } from "../../api/client";
import type { JobRequirements } from "../../types";
import { Button, ErrorState, Field, ListEditor, Loading, PageHeader, Panel, inputCls } from "../../components/ui";
import { useAsync } from "../../state/useAsync";

export default function Requirements() {
  const { jobId = "" } = useParams();
  const nav = useNavigate();
  const jobs = useAsync(() => api.listJobs(), [jobId]);
  const job = jobs.data?.find((j) => j.job_id === jobId);
  const [req, setReq] = useState<JobRequirements | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<Error | null>(null);
  useEffect(() => { if (job) setReq(job.requirements); }, [job]);
  const set = <K extends keyof JobRequirements>(k: K, v: JobRequirements[K]) => setReq((r) => (r ? { ...r, [k]: v } : r));

  if (jobs.loading) return <Loading />;
  if (jobs.error) return <ErrorState error={jobs.error} onRetry={jobs.reload} />;
  if (!job || !req) return <Panel>Job not found. <Link to="/recruiter/jobs" className="font-semibold text-brand">Back to jobs</Link></Panel>;

  async function confirm() {
    setBusy(true); setErr(null);
    try { await api.updateJob(jobId, { requirements: req!, status: "active" }); nav(`/recruiter/jobs/${jobId}/discover`); }
    catch (e) { setErr(e as Error); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Review requirements" sub={`${req.title} — confirm before discovery.`} />
      <Panel className="mb-6 bg-brand-soft"><p className="flex gap-2 text-sm"><ShieldAlert size={18} className="shrink-0 text-brand" aria-hidden />Only confirmed <strong>must-have</strong> requirements and <strong>dealbreakers</strong> are hard filters. Preferred items only influence ranking.</p></Panel>
      <div className="grid gap-6">
        <Panel><h2 className="mb-4 text-lg font-semibold">Role</h2><div className="grid gap-5 sm:grid-cols-2">
          <Field label="Title"><input className={inputCls} value={req.title} onChange={(e) => set("title", e.target.value)} /></Field>
          <Field label="Seniority"><input className={inputCls} value={req.seniority ?? ""} onChange={(e) => set("seniority", e.target.value || null)} /></Field>
          <Field label="Min years"><input type="number" min={0} className={inputCls} value={req.min_experience_years ?? ""} onChange={(e) => set("min_experience_years", e.target.value === "" ? null : Number(e.target.value))} /></Field>
          <Field label="Max years"><input type="number" min={0} className={inputCls} value={req.max_experience_years ?? ""} onChange={(e) => set("max_experience_years", e.target.value === "" ? null : Number(e.target.value))} /></Field>
          <ListEditor label="Locations" values={req.locations} onChange={(v) => set("locations", v)} />
          <ListEditor label="Work modes" values={req.work_modes} onChange={(v) => set("work_modes", v)} />
        </div></Panel>
        <Panel><h2 className="mb-1 text-lg font-semibold text-positive">Must-have (hard filters)</h2><p className="mb-4 text-sm text-muted">Candidates missing any of these are excluded.</p><div className="grid gap-5 sm:grid-cols-2">
          <ListEditor label="Skills" values={req.must_have_skills} onChange={(v) => set("must_have_skills", v)} />
          <ListEditor label="Qualifications" values={req.mandatory_qualifications} onChange={(v) => set("mandatory_qualifications", v)} />
          <ListEditor label="Required candidate fields" values={req.required_fields} onChange={(v) => set("required_fields", v)} />
        </div></Panel>
        <Panel><h2 className="mb-1 text-lg font-semibold">Preferred (soft)</h2><p className="mb-4 text-sm text-muted">Adjacent-fit candidates may miss these.</p><div className="grid gap-5 sm:grid-cols-2">
          <ListEditor label="Skills" values={req.preferred_skills} onChange={(v) => set("preferred_skills", v)} />
          <ListEditor label="Qualifications" values={req.preferred_qualifications} onChange={(v) => set("preferred_qualifications", v)} />
        </div></Panel>
        <Panel><h2 className="mb-1 text-lg font-semibold text-danger">Dealbreakers</h2><ListEditor label="Explicit dealbreakers" values={req.dealbreakers} onChange={(v) => set("dealbreakers", v)} /></Panel>
        <Panel className="border-adjacent"><h2 className="mb-2 flex items-center gap-2 text-lg font-semibold"><AlertCircle size={18} aria-hidden /> Needs confirmation</h2>
          {req.unknown_or_needs_confirmation.length === 0 ? <p className="text-sm text-muted">Nothing flagged as ambiguous.</p> : (
            <ul className="list-disc space-y-1 pl-5 text-sm">{req.unknown_or_needs_confirmation.map((u, i) => <li key={i}>{u}</li>)}</ul>)}
          <p className="mt-2 text-xs text-muted">Resolve these by editing the fields above, then confirm.</p></Panel>
      </div>
      {err && <div className="mt-4"><ErrorState error={err} /></div>}
      <div className="mt-6 flex gap-3"><Button size="lg" onClick={confirm} disabled={busy || !req.title.trim()}>{busy ? "Saving…" : "Confirm and start discovery"}</Button></div>
    </>
  );
}
