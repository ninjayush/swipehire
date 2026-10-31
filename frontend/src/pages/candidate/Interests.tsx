import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, X } from "lucide-react";
import { api } from "../../api/client";
import { Button, Chip, Empty, ErrorState, Loading, Panel } from "../../components/ui";
import { useAsync } from "../../state/useAsync";
import { useSession } from "../../state/session";

export default function CInterests() {
  const { candidateId } = useSession();
  const q = useAsync(() => (candidateId ? api.interests(candidateId) : Promise.resolve([])), [candidateId]);
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  if (!candidateId) return <Empty title="Create a profile first" action={<Link to="/candidate/onboarding"><Button>Create profile</Button></Link>} />;

  async function respond(id: string, r: "accept" | "reject") {
    setBusy(id); setErr(null);
    try { await api.respond(id, r); await q.reload(); } catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  }
  return (
    <div className="space-y-4 pt-2"><h1 className="text-2xl font-bold">Recruiter interest</h1>
      {err && <div role="alert" className="rounded-xl bg-danger-soft p-3 text-sm text-danger">{err}</div>}
      {q.loading ? <Loading /> : q.error ? <ErrorState error={q.error} onRetry={q.reload} /> : !q.data?.length ? <Empty title="No interest yet">When a recruiter expresses interest, it shows up here.</Empty> : q.data.map((i) => (
        <Panel key={i.interest_id} className="space-y-3 !p-5">
          <div className="flex items-start justify-between gap-2"><div><h2 className="font-semibold">{i.job_title}</h2>{i.created_at && <p className="text-xs text-muted">{new Date(i.created_at).toLocaleDateString()}</p>}</div>
            <Chip tone={i.status === "accepted" ? "positive" : i.status === "pending" ? "brand" : "neutral"}>{i.status === "rejected" ? "Declined" : i.status === "accepted" ? "Accepted" : "Pending"}</Chip></div>
          {i.status === "pending" && <div className="flex gap-3"><Button variant="secondary" size="lg" className="flex-1" disabled={busy === i.interest_id} onClick={() => respond(i.interest_id, "reject")}><X size={18} aria-hidden /> Decline</Button><Button size="lg" className="flex-1" disabled={busy === i.interest_id} onClick={() => respond(i.interest_id, "accept")}><Check size={18} aria-hidden /> Accept</Button></div>}
        </Panel>))}
    </div>
  );
}
