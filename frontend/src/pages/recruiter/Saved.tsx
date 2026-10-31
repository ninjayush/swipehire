import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { Avatar, Button, Empty, PageHeader, Panel } from "../../components/ui";
import { CandidateCard, FitBadge, MembershipBadge } from "../../components/CandidateCard";
import { getSaved, removeSaved } from "../../state/saved";

export default function Saved() {
  const [list, setList] = useState(getSaved);
  const [open, setOpen] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function shortlist(job_id: string, pid: string) {
    try { await api.recordAction(job_id, pid, "shortlist"); removeSaved(job_id, pid); setList(getSaved()); } catch (e) { setErr((e as Error).message); }
  }
  return (
    <>
      <PageHeader title="Saved candidates" sub="Saved for later — no interest has been expressed." />
      <p className="mb-4 text-xs text-muted">This list is kept in this browser (the backend has no saved-list endpoint yet).</p>
      {err && <div role="alert" className="mb-3 rounded-xl bg-danger-soft p-3 text-sm text-danger">{err}</div>}
      {!list.length ? <Empty title="Nothing saved" action={<Link to="/recruiter/jobs" className="font-semibold text-brand">Open a deck</Link>} /> : (
        <div className="space-y-3">{list.map((s) => {
          const k = `${s.job_id}:${s.card.person.person_id}`; const p = s.card.person;
          return (
            <Panel key={k} className="!p-5">
              <div className="flex flex-wrap items-center gap-4"><Avatar name={p.name} />
                <div className="flex-1"><div className="font-semibold">{p.name}</div><div className="text-sm text-muted">{p.current_title} · for {s.job_title}</div>
                  <div className="mt-2 flex gap-2"><MembershipBadge registered={p.membership_status === "registered"} /><FitBadge type={s.card.evaluation.fit_type} /></div></div>
                <Button variant="ghost" onClick={() => setOpen(open === k ? null : k)}>{open === k ? "Hide" : "Details"}</Button>
                <Button onClick={() => shortlist(s.job_id, p.person_id)}>{p.membership_status === "registered" ? "Express interest" : "Shortlist"}</Button></div>
              {open === k && <div className="mt-4 border-t border-line"><CandidateCard card={s.card} /></div>}
            </Panel>);
        })}</div>)}
    </>
  );
}
