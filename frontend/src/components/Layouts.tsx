import { Bookmark, Briefcase, Building2, Handshake, Heart, LayoutDashboard, Settings, User, Users } from "lucide-react";
import { NavLink, Outlet, Link } from "react-router-dom";
import { useSession } from "../state/session";
import { USE_MOCKS } from "../api/client";
import { DemoBanner, cx } from "./ui";

const Logo = () => <Link to="/" className="flex items-center gap-2 text-lg font-extrabold tracking-tight"><span className="grid h-8 w-8 place-items-center rounded-xl bg-brand text-white">S</span>SwipeHire</Link>;

const rItems = [
  { to: "/recruiter", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/recruiter/jobs", label: "Jobs", icon: Briefcase },
  { to: "/recruiter/saved", label: "Saved", icon: Bookmark },
  { to: "/recruiter/interests", label: "Interests", icon: Heart },
  { to: "/recruiter/matches", label: "Matches", icon: Handshake },
  { to: "/recruiter/company", label: "Company", icon: Building2 },
  { to: "/recruiter/settings", label: "Settings", icon: Settings },
];

export function RecruiterLayout() {
  const { company } = useSession();
  return (
    <div className="flex min-h-full flex-col">
      {USE_MOCKS && <DemoBanner />}
      <div className="flex flex-1 flex-col md:flex-row">
        <aside className="border-line bg-surface md:w-60 md:shrink-0 md:border-r">
          <div className="flex items-center justify-between p-4 md:block md:p-6"><Logo />
            {company && <p className="mt-0 text-xs text-muted md:mt-3">{company.name}</p>}</div>
          <nav aria-label="Recruiter" className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:pb-0">
            {rItems.map(({ to, label, icon: I, end }) => (
              <NavLink key={to} to={to} end={end} className={({ isActive }) => cx("flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium", isActive ? "bg-brand-soft text-brand" : "text-ink/75 hover:bg-bg")}>
                <I size={18} aria-hidden />{label}</NavLink>))}
            <Link to="/candidate" className="mt-2 flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted hover:bg-bg md:mt-6"><User size={18} aria-hidden />Switch to candidate</Link>
          </nav>
        </aside>
        <main className="flex-1 px-4 py-6 md:px-10 md:py-10"><div className="mx-auto max-w-5xl"><Outlet /></div></main>
      </div>
    </div>
  );
}

const cItems = [
  { to: "/candidate", label: "Home", icon: LayoutDashboard, end: true },
  { to: "/candidate/profile", label: "Profile", icon: User },
  { to: "/candidate/interests", label: "Interests", icon: Heart },
  { to: "/candidate/matches", label: "Matches", icon: Users },
];

export function CandidateLayout() {
  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col bg-bg">
      {USE_MOCKS && <DemoBanner />}
      <header className="flex items-center justify-between px-5 py-4"><Logo /><Link to="/recruiter" className="text-xs text-muted underline">Recruiter view</Link></header>
      <main className="flex-1 px-5 pb-28"><Outlet /></main>
      <nav aria-label="Candidate" className="safe-bottom fixed inset-x-0 bottom-0 z-20 mx-auto flex max-w-md justify-around border-t border-line bg-surface pt-2">
        {cItems.map(({ to, label, icon: I, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => cx("flex min-h-12 min-w-16 flex-col items-center justify-center gap-0.5 rounded-xl px-3 text-xs font-medium", isActive ? "text-brand" : "text-muted")}>
            <I size={22} aria-hidden />{label}</NavLink>))}
      </nav>
    </div>
  );
}
