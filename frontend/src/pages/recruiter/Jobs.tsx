import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { api } from "../../api/client";
import { Button, Chip, Empty, ErrorState, Loading, PageHeader, Panel } from "../../components/ui";
import { useAsync } from "../../state/useAsync";
import { useSession } from "../../state/session";

export default function Jobs() {
  const { company } = useSession();
  const jobs = useAsync(() => api.listJobs(company?.id), [company?.id]);
  return (
    <>
      <PageHeader title="Jobs" action={<Link to="/recruiter/jobs/new"><Button><Plus size={16} aria-hidden /> New job</Button></Link>} />
      {jobs.loading ? <Loading /> : jobs.error ? <ErrorState error={jobs.error} onRetry={jobs.reload} /> : !jobs.data?.length ? <Empty title="No jobs yet" /> : (
        <div className="space-y-3">{jobs.data.map((j) => (
          <Panel key={j.job_id} className="flex flex-wrap items-center justify-between gap-3 !p-5">
            <div><div className="flex items-center gap-2"><h2 className="font-semibold">{j.title}</h2><Chip tone={j.status === "active" ? "positive" : "neutral"}>{j.status.replace(/_/g, " ")}</Chip></div>
              <p className="text-sm text-muted">{j.requirements.locations.join(", ") || "Location not set"}</p></div>
            <div className="flex gap-2">
              <Link to={`/recruiter/jobs/${j.job_id}/requirements`}><Button variant="ghost">Requirements</Button></Link>
              <Link to={`/recruiter/jobs/${j.job_id}/shortlist`}><Button variant="secondary">Shortlist</Button></Link>
              <Link to={`/recruiter/jobs/${j.job_id}/deck`}><Button>Deck</Button></Link>
            </div></Panel>))}</div>)}
    </>
  );
}
