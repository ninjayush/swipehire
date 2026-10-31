import { Link } from "react-router-dom";
import { Plus, ArrowRight } from "lucide-react";
import { api } from "../../api/client";
import { Button, Chip, Empty, ErrorState, Loading, PageHeader, Panel } from "../../components/ui";
import { useAsync } from "../../state/useAsync";
import { useSession } from "../../state/session";

export default function Dashboard() {
  const { company } = useSession();
  const jobs = useAsync(() => api.listJobs(company?.id), [company?.id]);
  return (
    <>
      <PageHeader title={company ? `Welcome, ${company.name}` : "Welcome to SwipeHire"} sub="Your roles and discovery progress."
        action={<Link to="/recruiter/jobs/new"><Button size="lg"><Plus size={18} aria-hidden /> Create job</Button></Link>} />
      {!company && <Panel className="mb-6 bg-brand-soft"><p className="font-medium">Start by confirming your company.</p><Link to="/recruiter/company" className="mt-2 inline-flex items-center gap-1 font-semibold text-brand">Set up company <ArrowRight size={16} aria-hidden /></Link></Panel>}
      {jobs.loading ? <Loading /> : jobs.error ? <ErrorState error={jobs.error} onRetry={jobs.reload} /> :
        !jobs.data?.length ? <Empty title="No jobs yet" action={<Link to="/recruiter/jobs/new"><Button>Create your first job</Button></Link>}>Paste a job description or build one with structured fields.</Empty> : (
          <div className="grid gap-4 sm:grid-cols-2">
            {jobs.data.slice(0, 6).map((j) => (
              <Panel key={j.job_id}>
                <div className="flex items-start justify-between gap-2"><h2 className="text-lg font-semibold">{j.title}</h2><Chip tone={j.status === "active" ? "positive" : "neutral"}>{j.status.replace(/_/g, " ")}</Chip></div>
                <p className="mt-1 text-sm text-muted">{j.requirements.must_have_skills.slice(0, 4).join(" · ") || "No must-have skills listed"}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link to={`/recruiter/jobs/${j.job_id}/deck`}><Button variant="secondary">Open deck</Button></Link>
                  <Link to={`/recruiter/jobs/${j.job_id}/requirements`}><Button variant="ghost">Requirements</Button></Link>
                </div>
              </Panel>))}
          </div>)}
    </>
  );
}
