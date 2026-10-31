import { Link, useParams } from "react-router-dom";
import { SlidersHorizontal } from "lucide-react";
import { api } from "../../api/client";
import type { DeckCard, RecruiterAction } from "../../types";
import { SwipeDeck } from "../../components/SwipeDeck";
import { Button, Chip, Empty, ErrorState, Loading } from "../../components/ui";
import { ApiError } from "../../api/http";
import { useAsync } from "../../state/useAsync";
import { addSaved } from "../../state/saved";

export default function Deck() {
  const { jobId = "" } = useParams();
  const deck = useAsync(() => api.getDeck(jobId), [jobId]);
  const jobs = useAsync(() => api.listJobs(), [jobId]);
  const job = jobs.data?.find((j) => j.job_id === jobId);

  const onAction = async (card: DeckCard, action: RecruiterAction) => {
    await api.recordAction(jobId, card.person.person_id, action);
    if (action === "save") addSaved({ job_id: jobId, job_title: job?.title ?? "Role", card, at: new Date().toISOString() });
  };

  if (deck.loading) return <Loading label="Loading candidates…" />;
  if (deck.error) {
    const notRun = deck.error instanceof ApiError ? deck.error.kind === "not_found" : (deck.error as { kind?: string }).kind === "not_found";
    return notRun
      ? <Empty title="No candidates yet" action={<Link to={`/recruiter/jobs/${jobId}/discover`}><Button size="lg">Run discovery</Button></Link>}>Discovery hasn't been run for this job.</Empty>
      : <ErrorState error={deck.error} onRetry={deck.reload} />;
  }
  const d = deck.data!;
  if (d.status === "processing") return <Loading label="Discovery is still processing…" />;
  if (d.status === "failed") return <ErrorState error={new Error("The last discovery run failed.")} onRetry={() => void api.discover(jobId).then(deck.reload)} />;

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_260px]">
      <div>
        <div className="mb-4"><h1 className="text-xl font-bold">{job?.title ?? "Candidate deck"}</h1></div>
        {d.cards.length === 0 ? (
          <Empty title="No eligible candidates" action={<Link to={`/recruiter/jobs/${jobId}/requirements`}><Button variant="secondary">Review requirements</Button></Link>}>Nobody met every must-have requirement. Consider loosening mandatory criteria.</Empty>
        ) : (
          <SwipeDeck cards={d.cards} onAction={onAction} onDone={
            <Empty title="You've reviewed everyone" action={<div className="flex gap-2"><Link to={`/recruiter/jobs/${jobId}/shortlist`}><Button>View shortlist</Button></Link><Link to={`/recruiter/jobs/${jobId}/requirements`}><Button variant="secondary">Job requirements</Button></Link></div>}>That's the full deck for this run.</Empty>} />)}
      </div>
      <aside className="space-y-4 lg:pt-12" aria-label="Job fit summary">
        <div className="rounded-3xl border border-line bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold"><SlidersHorizontal size={16} aria-hidden /> This run</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-muted">Considered</dt><dd className="font-semibold">{d.total_candidates}</dd></div>
            <div className="flex justify-between"><dt className="text-muted">Direct fit</dt><dd className="font-semibold">{d.direct_count}</dd></div>
            <div className="flex justify-between"><dt className="text-muted">Adjacent fit</dt><dd className="font-semibold">{d.adjacent_count}</dd></div>
            <div className="flex justify-between"><dt className="text-muted">Excluded</dt><dd className="font-semibold">{d.excluded_count}</dd></div>
          </dl>
        </div>
        {job && <div className="rounded-3xl border border-line bg-surface p-5"><h2 className="mb-2 text-sm font-semibold">Must-haves</h2>
          <div className="flex flex-wrap gap-1.5">{job.requirements.must_have_skills.map((s) => <Chip key={s} tone="positive">{s}</Chip>)}</div>
          <Link to={`/recruiter/jobs/${jobId}/requirements`} className="mt-3 inline-block text-sm font-semibold text-brand">Edit requirements</Link></div>}
        <Link to={`/recruiter/jobs/${jobId}/shortlist`} className="block"><Button variant="secondary" className="w-full">View shortlist</Button></Link>
      </aside>
    </div>
  );
}
