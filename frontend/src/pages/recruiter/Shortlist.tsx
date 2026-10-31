import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { Avatar, Empty, ErrorState, Loading, PageHeader, Panel } from "../../components/ui";
import { FitBadge, MembershipBadge } from "../../components/CandidateCard";
import { useAsync } from "../../state/useAsync";

export default function Shortlist() {
  const { jobId = "" } = useParams();
  const list = useAsync(() => api.shortlist(jobId), [jobId]);
  const deck = useAsync(() => api.getDeck(jobId).catch(() => null), [jobId]);
  const matches = useAsync(() => api.matches({ job_id: jobId }), [jobId]);
  const byId = new Map(deck.data?.cards.map((c) => [c.person.person_id, c]) ?? []);
  const matched = new Set(matches.data?.map((m) => m.person_id));

  return (
    <>
      <PageHeader title="Shortlist" sub="Candidates you've shortlisted or expressed interest in." />
      {list.loading ? <Loading /> : list.error ? <ErrorState error={list.error} onRetry={list.reload} /> : !list.data?.length ? (
        <Empty title="Nobody shortlisted yet" action={<Link className="font-semibold text-brand" to={`/recruiter/jobs/${jobId}/deck`}>Go to deck</Link>} />
      ) : (
        <div className="space-y-3">{list.data.map((e) => {
          const c = byId.get(e.person_id); const member = e.membership_status === "registered";
          return (
            <Panel key={e.person_id} className="flex flex-wrap items-center gap-4 !p-5">
              <Avatar name={e.name} />
              <div className="min-w-0 flex-1"><div className="font-semibold">{e.name ?? "Unnamed"}</div>
                <div className="text-sm text-muted">{c?.person.current_title ?? "Role unknown"}{c?.evaluation.fit_score != null && ` · fit ${Math.round(c.evaluation.fit_score)}`}</div>
                <div className="mt-2 flex flex-wrap gap-2"><MembershipBadge registered={member} /><FitBadge type={c?.evaluation.fit_type} />
                  <span className="rounded-full bg-bg px-3 py-1 text-sm">{!member ? "Internal shortlist" : matched.has(e.person_id) ? "Mutual match" : "Interest sent — awaiting response"}</span></div></div>
            </Panel>);
        })}</div>)}
    </>
  );
}
