import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { DECK, DeckCard, DEMO_CANDIDATE_ID, JOB_TITLE } from "./data";
import { api, InterestRow, Job, MatchRow, USE_MOCKS } from "./api";

export type Role = "recruiter" | "candidate" | null;
export interface Row { id: string; kind: "shortlist" | "save"; name: string; member: boolean; title?: string; score?: number }
type Act = "shortlist" | "pass" | "save";

interface Store {
  live: boolean; role: Role; setRole: (r: Role) => void;
  loading: boolean; error: string | null; reload: () => void;
  jobs: Job[]; job: { id: string; title: string } | null; selectJob: (j: Job | null) => void;
  cards: DeckCard[]; act: (card: DeckCard, a: Act) => Promise<void>; rows: Row[];
  candidateId: string | null; setCandidateId: (id: string | null) => void;
  interests: InterestRow[]; respond: (id: string, r: "accept" | "reject") => Promise<void>;
  matches: MatchRow[];
}
const Ctx = createContext<Store | null>(null);
export const useStore = () => { const s = useContext(Ctx); if (!s) throw new Error("no store"); return s; };
const msg = (e: unknown) => (e instanceof Error ? e.message : String(e));

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const live = !USE_MOCKS;
  const [role, setRoleState] = useState<Role>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [job, setJob] = useState<Store["job"]>(live ? null : { id: "demo", title: JOB_TITLE });
  const [cards, setCards] = useState<DeckCard[]>(live ? [] : DECK);
  const [rows, setRows] = useState<Row[]>([]);
  const [candidateId, setCandidateId] = useState<string | null>(live ? null : DEMO_CANDIDATE_ID);
  const [interests, setInterests] = useState<InterestRow[]>([]);
  const [matches, setMatches] = useState<MatchRow[]>([]);
  // mock-mode in-memory backing
  const [mockInterests, setMockInterests] = useState<InterestRow[]>([]);

  const guard = useCallback(async (fn: () => Promise<void>) => { setLoading(true); setError(null); try { await fn(); } catch (e) { setError(msg(e)); } finally { setLoading(false); } }, []);

  const refreshRecruiter = useCallback(async (jobId: string) => {
    const [sl, ms] = await Promise.all([api.shortlist(jobId), api.matches({ job_id: jobId })]);
    setRows(sl.map((s) => ({ id: s.person_id, kind: "shortlist", name: s.name, member: s.member })));
    setMatches(ms);
  }, []);
  const refreshCandidate = useCallback(async (id: string) => {
    const [i, m] = await Promise.all([api.interests(id), api.matches({ person_id: id })]);
    setInterests(i); setMatches(m);
  }, []);

  const reload = useCallback(() => {
    if (!live) return;
    void guard(async () => {
      if (role === "recruiter") { if (job) { setCards(await api.deckFor(job.id)); await refreshRecruiter(job.id); } else setJobs(await api.listJobs()); }
      if (role === "candidate" && candidateId) await refreshCandidate(candidateId);
    });
  }, [live, role, job, candidateId, guard, refreshRecruiter, refreshCandidate]);

  useEffect(() => { reload(); }, [role, job?.id, candidateId]); // eslint-disable-line react-hooks/exhaustive-deps

  const selectJob = useCallback((j: Job | null) => { setCards([]); setRows([]); setJob(j ? { id: j.job_id, title: j.title } : null); }, []);
  const setRole = useCallback((r: Role) => { setError(null); setRoleState(r); }, []);

  const act = useCallback(async (card: DeckCard, a: Act) => {
    const id = card.person.person_id;
    if (live) {
      if (!job) return;
      await api.action(job.id, id, a); // throws on failure -> deck keeps the card
      if (a !== "pass") setRows((l) => [...l.filter((r) => r.id !== id), { id, kind: a === "save" ? "save" : "shortlist", name: card.person.name, member: card.person.member, title: card.person.current_title, score: card.ev.fit_score }]);
      if (a === "shortlist") api.matches({ job_id: job.id }).then(setMatches).catch(() => {});
      return;
    }
    if (a !== "pass") setRows((l) => [...l.filter((r) => r.id !== id), { id, kind: a === "save" ? "save" : "shortlist", name: card.person.name, member: card.person.member, title: card.person.current_title, score: card.ev.fit_score }]);
    // Only registered members receive interest. Non-members: internal shortlist, nobody is notified.
    if (a === "shortlist" && card.person.member) setMockInterests((l) => l.some((i) => i.id === `i-${id}`) ? l : [...l, { id: `i-${id}`, job_title: JOB_TITLE, status: "pending", at: new Date().toISOString() }]);
  }, [live, job]);

  const respond = useCallback(async (id: string, r: "accept" | "reject") => {
    if (live) { await api.respond(id, r); if (candidateId) await refreshCandidate(candidateId); return; }
    setMockInterests((l) => l.map((i) => (i.id === id ? { ...i, status: r === "accept" ? "accepted" : "rejected" } : i)));
  }, [live, candidateId, refreshCandidate]);

  const value = useMemo<Store>(() => ({
    live, role, setRole, loading, error, reload, jobs, job, selectJob, cards, act, rows, candidateId, setCandidateId,
    interests: live ? interests : mockInterests,
    respond,
    matches: live ? matches : mockInterests.filter((i) => i.status === "accepted").map((i) => ({ id: i.id, name: "Asha Verma", job_title: i.job_title, person_id: DEMO_CANDIDATE_ID })),
  }), [live, role, setRole, loading, error, reload, jobs, job, selectJob, cards, act, rows, candidateId, interests, mockInterests, respond, matches]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
