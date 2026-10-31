import { Link } from "react-router-dom";
import { ArrowRight, Smartphone, Monitor } from "lucide-react";
import { USE_MOCKS } from "../api/client";
import { DemoBanner } from "../components/ui";

export default function Landing() {
  return (
    <div className="min-h-full">
      {USE_MOCKS && <DemoBanner />}
      <div className="mx-auto max-w-4xl px-6 py-16 sm:py-24">
        <div className="mb-10 flex items-center gap-2 text-xl font-extrabold"><span className="grid h-9 w-9 place-items-center rounded-xl bg-brand text-white">S</span>SwipeHire</div>
        <h1 className="max-w-2xl text-4xl font-bold leading-tight tracking-tight sm:text-5xl">Discover talent beyond keywords.</h1>
        <p className="mt-4 max-w-xl text-lg text-muted">Turn a job description into an explainable, swipeable candidate deck — including qualified adjacent-fit people keyword search would miss.</p>
        <div className="mt-12 grid gap-4 sm:grid-cols-2">
          <Link to="/recruiter" className="group rounded-3xl border border-line bg-surface p-6 shadow-sm hover:border-brand">
            <Monitor className="text-brand" aria-hidden /><h2 className="mt-4 text-xl font-semibold">I'm a recruiter</h2>
            <p className="mt-1 text-sm text-muted">Create a role, review requirements, swipe through ranked candidates.</p>
            <span className="mt-4 inline-flex items-center gap-1 font-semibold text-brand">Enter demo <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" aria-hidden /></span>
          </Link>
          <Link to="/candidate" className="group rounded-3xl border border-line bg-surface p-6 shadow-sm hover:border-brand">
            <Smartphone className="text-brand" aria-hidden /><h2 className="mt-4 text-xl font-semibold">I'm a candidate</h2>
            <p className="mt-1 text-sm text-muted">Build your profile, upload a resume, respond to recruiter interest.</p>
            <span className="mt-4 inline-flex items-center gap-1 font-semibold text-brand">Enter demo <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" aria-hidden /></span>
          </Link>
        </div>
        <p className="mt-8 text-xs text-muted">Demo entry only — no real sign-in. No emails, messages or outreach are ever sent.</p>
      </div>
    </div>
  );
}
