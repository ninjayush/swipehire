import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { api } from "../../api/client";
import { Button, ErrorState, PageHeader, Panel } from "../../components/ui";

export default function Discover() {
  const { jobId = "" } = useParams();
  const nav = useNavigate();
  const [err, setErr] = useState<Error | null>(null);
  const started = useRef(false);
  const [n, setN] = useState(0);

  const run = () => { setErr(null); api.discover(jobId).then(() => nav(`/recruiter/jobs/${jobId}/deck`, { replace: true })).catch((e) => setErr(e)); };
  useEffect(() => { if (started.current) return; started.current = true; run(); }, []); // eslint-disable-line
  useEffect(() => { const t = setInterval(() => setN((x) => x + 1), 1800); return () => clearInterval(t); }, []);
  const steps = ["Gathering registered candidates", "Searching Crustdata-sourced professionals", "Applying must-have requirements", "Scoring and ranking"];

  return (
    <>
      <PageHeader title="Discovery" />
      {err ? <><ErrorState error={err} onRetry={() => { started.current = true; run(); }} /><Link to={`/recruiter/jobs/${jobId}/requirements`} className="mt-4 inline-block"><Button variant="secondary">Back to requirements</Button></Link></> : (
        <Panel className="grid place-items-center py-16 text-center" aria-live="polite">
          <Loader2 className="animate-spin text-brand" size={36} aria-hidden />
          <h2 className="mt-4 text-xl font-semibold">Finding your candidates…</h2>
          <p className="mt-2 text-muted">{steps[Math.min(n, steps.length - 1)]}</p>
        </Panel>)}
    </>
  );
}
