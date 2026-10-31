import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { USE_MOCKS } from "../../api/client";
import { Button, Field, Panel, inputCls } from "../../components/ui";
import { useSession } from "../../state/session";

export default function CHome() {
  const { candidateId, setCandidateId } = useSession();
  const [id, setId] = useState("");
  return (
    <div className="space-y-5 pt-2">
      <h1 className="text-3xl font-bold leading-tight tracking-tight">Let the right roles come to you.</h1>
      <p className="text-muted">Build your profile once. Recruiters express interest; you decide who to talk to.</p>
      {candidateId ? (
        <Panel className="space-y-3 !p-5"><p className="text-sm text-muted">Signed in as demo candidate</p><p className="font-mono text-sm">{candidateId}</p>
          <Link to="/candidate/interests"><Button size="lg" className="w-full">See recruiter interest</Button></Link>
          <Link to="/candidate/profile"><Button variant="secondary" className="w-full">View my profile</Button></Link>
          <button className="text-xs text-muted underline" onClick={() => setCandidateId(null)}>Switch demo candidate</button></Panel>
      ) : (
        <Panel className="space-y-4 !p-5">
          <Link to="/candidate/onboarding"><Button size="lg" className="w-full">Create my profile <ArrowRight size={18} aria-hidden /></Button></Link>
          {USE_MOCKS && <Button variant="secondary" className="w-full" onClick={() => setCandidateId("demo-asha")}>Continue as demo candidate (Asha)</Button>}
          <div className="border-t border-line pt-4"><Field label="Already registered? Enter candidate ID"><input className={inputCls} value={id} onChange={(e) => setId(e.target.value)} /></Field>
            <Button variant="ghost" className="mt-2" disabled={!id.trim()} onClick={() => setCandidateId(id.trim())}>Continue</Button></div>
        </Panel>)}
      <p className="text-xs text-muted">Demo entry — there is no real sign-in. Nobody outside this app is ever contacted.</p>
    </div>
  );
}
