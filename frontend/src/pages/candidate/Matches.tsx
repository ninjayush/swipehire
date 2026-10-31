import { Link } from "react-router-dom";
import { Handshake } from "lucide-react";
import { api } from "../../api/client";
import { Button, Empty, ErrorState, Loading, Panel } from "../../components/ui";
import { useAsync } from "../../state/useAsync";
import { useSession } from "../../state/session";

export default function CMatches() {
  const { candidateId } = useSession();
  const q = useAsync(() => (candidateId ? api.matches({ person_id: candidateId }) : Promise.resolve([])), [candidateId]);
  if (!candidateId) return <Empty title="Create a profile first" action={<Link to="/candidate/onboarding"><Button>Create profile</Button></Link>} />;
  return (
    <div className="space-y-4 pt-2"><h1 className="text-2xl font-bold">Your matches</h1>
      {q.loading ? <Loading /> : q.error ? <ErrorState error={q.error} onRetry={q.reload} /> : !q.data?.length ? <Empty title="No matches yet">A match happens when you accept a recruiter's interest.</Empty> : q.data.map((m) => (
        <Panel key={m.match_id} className="flex items-center gap-4 !p-5"><Handshake className="text-positive" aria-hidden /><div><h2 className="font-semibold">{m.job_title}</h2><p className="text-sm text-muted">It's a match{m.created_at && ` · ${new Date(m.created_at).toLocaleDateString()}`}</p></div></Panel>))}
      <p className="text-xs text-muted">Messaging isn't part of this MVP — nothing is sent outside the app.</p>
    </div>
  );
}
