import { api } from "../../api/client";
import { Avatar, Chip, Empty, ErrorState, Loading, PageHeader, Panel } from "../../components/ui";
import { useAsync } from "../../state/useAsync";
import { useSession } from "../../state/session";

export default function RInterests() {
  const { company } = useSession();
  const q = useAsync(async () => {
    const jobs = await api.listJobs(company?.id);
    const matches = await api.matches();
    const rows = (await Promise.all(jobs.map(async (j) => (await api.shortlist(j.job_id)).filter((s) => s.membership_status === "registered").map((s) => ({ job: j, s }))))).flat();
    return { rows, matched: new Set(matches.map((m) => `${m.job_id}:${m.person_id}`)) };
  }, [company?.id]);
  return (
    <>
      <PageHeader title="Interests" sub="Interest you've sent to registered candidates. Non-members never appear here." />
      {q.loading ? <Loading /> : q.error ? <ErrorState error={q.error} onRetry={q.reload} /> : !q.data?.rows.length ? <Empty title="No pending interests">Express interest in a registered candidate from a deck.</Empty> : (
        <div className="space-y-3">{q.data.rows.map(({ job, s }) => {
          const m = q.data!.matched.has(`${job.job_id}:${s.person_id}`);
          return <Panel key={`${job.job_id}:${s.person_id}`} className="flex items-center gap-4 !p-5"><Avatar name={s.name} /><div className="flex-1"><div className="font-semibold">{s.name}</div><div className="text-sm text-muted">{job.title}</div></div>
            {m ? <Chip tone="positive">Mutual match</Chip> : <Chip tone="brand">Awaiting response</Chip>}</Panel>;
        })}</div>)}
      <p className="mt-4 text-xs text-muted">A declined interest is not exposed to recruiters by the backend yet; it simply never becomes a match.</p>
    </>
  );
}
