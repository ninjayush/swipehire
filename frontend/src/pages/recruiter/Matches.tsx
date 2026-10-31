import { Handshake } from "lucide-react";
import { api } from "../../api/client";
import { Avatar, Empty, ErrorState, Loading, PageHeader, Panel } from "../../components/ui";
import { useAsync } from "../../state/useAsync";

export default function RMatches() {
  const q = useAsync(() => api.matches(), []);
  return (
    <>
      <PageHeader title="Mutual matches" sub="Created only when a registered candidate accepts your interest." />
      {q.loading ? <Loading /> : q.error ? <ErrorState error={q.error} onRetry={q.reload} /> : !q.data?.length ? <Empty title="No matches yet">Matches appear after a candidate accepts.</Empty> : (
        <div className="space-y-3">{q.data.map((m) => (
          <Panel key={m.match_id} className="flex items-center gap-4 !p-5"><Avatar name={m.candidate_name} /><div className="flex-1"><div className="font-semibold">{m.candidate_name}</div><div className="text-sm text-muted">{m.job_title}{m.created_at && ` · ${new Date(m.created_at).toLocaleDateString()}`}</div></div><Handshake className="text-positive" aria-label="Mutual match" /></Panel>))}</div>)}
    </>
  );
}
