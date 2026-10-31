import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { Avatar, Button, Chip, Empty, ErrorState, Loading, Panel } from "../../components/ui";
import { useAsync } from "../../state/useAsync";
import { useSession } from "../../state/session";
import type { Rec } from "../../types";

const s = (v: unknown) => (typeof v === "string" || typeof v === "number" ? String(v) : "");

export default function CProfile() {
  const { candidateId } = useSession();
  const q = useAsync(() => (candidateId ? api.getCandidate(candidateId) : Promise.resolve(null)), [candidateId]);
  if (!candidateId) return <Empty title="No profile yet" action={<Link to="/candidate/onboarding"><Button>Create profile</Button></Link>} />;
  if (q.loading) return <Loading />;
  if (q.error) return <ErrorState error={q.error} onRetry={q.reload} />;
  const p = q.data!;
  const prefs = Object.entries(p.candidate_preferences);
  return (
    <div className="space-y-4 pt-2">
      <div className="flex items-center gap-4"><Avatar name={p.name} size={64} /><div><h1 className="text-2xl font-bold">{p.name ?? "Unnamed"}</h1><p className="text-muted">{p.headline ?? "No headline"}</p></div></div>
      <Panel className="space-y-2 !p-5 text-sm"><div><span className="text-muted">Role:</span> {p.current_title ? `${p.current_title}${p.current_company ? ` at ${p.current_company}` : ""}` : "Not available"}</div>
        <div><span className="text-muted">Location:</span> {p.location ?? "Not available"}</div>
        <div><span className="text-muted">Experience:</span> {p.experience_years != null ? `${p.experience_years} years` : "Not available"}</div></Panel>
      {p.skills.length > 0 && <Panel className="!p-5"><h2 className="mb-2 font-semibold">Skills</h2><div className="flex flex-wrap gap-2">{p.skills.map((k) => <Chip key={k}>{k}</Chip>)}</div></Panel>}
      {p.resume_highlights.length > 0 && <Panel className="!p-5"><h2 className="mb-2 font-semibold">Resume highlights</h2><ul className="space-y-2 text-sm">{p.resume_highlights.map((h: Rec, i) => <li key={i}><strong>{s(h.label)}</strong> {s(h.text) || s(h.summary)}</li>)}</ul></Panel>}
      <Panel className="!p-5"><h2 className="mb-2 font-semibold">Preferences</h2>{prefs.length === 0 ? <p className="text-sm text-muted">Unknown — not provided.</p> : <ul className="space-y-1 text-sm">{prefs.map(([k, v]) => <li key={k}><span className="text-muted">{k.replace(/_/g, " ")}:</span> {Array.isArray(v) ? v.join(", ") : s(v)}</li>)}</ul>}</Panel>
      <Link to="/candidate/onboarding"><Button variant="secondary" className="w-full">Update profile</Button></Link>
    </div>
  );
}
