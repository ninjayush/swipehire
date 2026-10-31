import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

interface Session {
  company: { id: string; name: string } | null;
  candidateId: string | null;
  setCompany: (c: Session["company"]) => void;
  setCandidateId: (id: string | null) => void;
}
const Ctx = createContext<Session | null>(null);
const load = <T,>(k: string, d: T): T => { try { return JSON.parse(localStorage.getItem(k) ?? "") as T; } catch { return d; } };

export function SessionProvider({ children }: { children: ReactNode }) {
  const [company, setCompanyState] = useState<Session["company"]>(() => load("sh.company", null));
  const [candidateId, setCid] = useState<string | null>(() => load("sh.candidate", null));
  useEffect(() => localStorage.setItem("sh.company", JSON.stringify(company)), [company]);
  useEffect(() => localStorage.setItem("sh.candidate", JSON.stringify(candidateId)), [candidateId]);
  const setCompany = useCallback((c: Session["company"]) => setCompanyState(c), []);
  const setCandidateId = useCallback((id: string | null) => setCid(id), []);
  return <Ctx.Provider value={{ company, candidateId, setCompany, setCandidateId }}>{children}</Ctx.Provider>;
}
export function useSession() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useSession outside provider");
  return v;
}
