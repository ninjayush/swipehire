// Mobile API client. Same contracts as frontend/src/api (backend schemas are the source of truth).
// Live mode never falls back to mock data.
import { DeckCard, Evaluation, Person } from "./data";

export const USE_MOCKS = process.env.EXPO_PUBLIC_USE_MOCKS === "true";
export const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error { constructor(public kind: "network" | "not_found" | "forbidden" | "validation" | "server", msg: string) { super(msg); } }

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try { res = await fetch(`${BASE_URL}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } }); }
  catch { throw new ApiError("network", `Can't reach the SwipeHire backend at ${BASE_URL}. Is it running, and is this address reachable from your device?`); }
  if (!res.ok) {
    let msg = res.statusText;
    try { const d = (await res.json()).detail; msg = typeof d === "string" ? d : JSON.stringify(d); } catch { /* keep */ }
    throw new ApiError(res.status === 404 ? "not_found" : res.status === 403 ? "forbidden" : res.status < 500 ? "validation" : "server", msg);
  }
  return (await res.json()) as T;
}
const post = <T,>(p: string, b?: unknown) => call<T>(p, { method: "POST", body: b === undefined ? undefined : JSON.stringify(b) });

type Rec = Record<string, unknown>;
const str = (v: unknown) => (typeof v === "string" || typeof v === "number" ? String(v) : "");
const arr = <T,>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : []);

export interface Job { job_id: string; title: string; status: string; must_have_skills: string[] }
export interface InterestRow { id: string; job_title: string; status: "pending" | "accepted" | "rejected"; at: string }
export interface MatchRow { id: string; name: string; job_title: string; person_id: string }
export interface ShortlistRow { person_id: string; name: string; member: boolean }

/** Backend card {person, evaluation} -> mobile DeckCard. Missing values stay null/empty (never invented). */
export function mapCard(raw: Rec): DeckCard {
  const p = (raw.person ?? raw) as Rec; const e = (raw.evaluation ?? raw) as Rec;
  const person: Person = {
    person_id: str(p.person_id), name: str(p.name) || "Name unavailable",
    headline: str(p.headline) || str(p.current_title), current_title: str(p.current_title), current_company: str(p.current_company),
    location: str(p.location) || null, skills: arr<string>(p.skills), experience_years: p.experience_years == null ? null : Number(p.experience_years),
    member: p.membership_status === "registered",
    history: arr<Rec>(p.employment_history).map((h) => ({ title: str(h.title) || str(h.job_title) || "Role", company: str(h.company), years: [str(h.start), str(h.end)].filter(Boolean).join(" – "), note: str(h.summary) || undefined })),
    education: arr<Rec>(p.education).map((x) => [str(x.degree), str(x.school)].filter(Boolean).join(", ")).filter(Boolean),
    prompts: arr<Rec>(p.resume_highlights).map((h) => ({ label: str(h.label) || "Highlight", text: str(h.text) || str(h.summary) || str(h.description) })).filter((x) => x.text),
  };
  const comps = (e.component_scores ?? {}) as Record<string, number>;
  const evaluation: Evaluation = {
    fit_score: e.fit_score == null ? 0 : Number(e.fit_score), fit_type: e.fit_type === "adjacent" ? "adjacent" : "direct",
    explanation: str(e.match_explanation) || "No explanation provided by the matching service.",
    components: Object.fromEntries(Object.entries(comps).map(([k, v]) => [k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase()), Number(v)])),
    coverage: e.evidence_coverage == null ? 0 : Number(e.evidence_coverage),
  };
  return { person, ev: evaluation };
}

export const api = {
  async listJobs(): Promise<Job[]> {
    const r = await call<{ jobs: Rec[] }>("/api/jobs");
    return r.jobs.map((j) => ({ job_id: str(j.job_id), title: str(j.title) || "Untitled role", status: str(j.status), must_have_skills: arr<string>((j.requirements as Rec | undefined)?.must_have_skills) }));
  },
  /** Fetch the latest deck; if none exists yet, run discovery (the backend pipeline) first. */
  async deckFor(jobId: string): Promise<DeckCard[]> {
    let raw: Rec;
    try { raw = await call<Rec>(`/api/jobs/${jobId}/deck`); }
    catch (e) { if (e instanceof ApiError && e.kind === "not_found") raw = await post<Rec>(`/api/jobs/${jobId}/discover`); else throw e; }
    if (raw.status === "failed") throw new ApiError("server", "The last discovery run failed.");
    return arr<Rec>(raw.cards).map(mapCard);
  },
  async rediscover(jobId: string): Promise<DeckCard[]> { return arr<Rec>((await post<Rec>(`/api/jobs/${jobId}/discover`)).cards).map(mapCard); },
  action: (jobId: string, person_id: string, action: "shortlist" | "pass" | "save") => post<Rec>(`/api/jobs/${jobId}/actions`, { person_id, action }),
  async shortlist(jobId: string): Promise<ShortlistRow[]> {
    const r = await call<{ shortlist: Rec[] }>(`/api/jobs/${jobId}/shortlist`);
    return r.shortlist.map((s) => ({ person_id: str(s.person_id), name: str(s.name) || "Unnamed", member: s.membership_status === "registered" }));
  },
  async candidate(id: string): Promise<Person> { const r = await call<{ person: Rec }>(`/api/candidates/${id}`); return mapCard({ person: r.person }).person; },
  async interests(personId: string): Promise<InterestRow[]> {
    const r = await call<{ interests: Rec[] }>(`/api/candidates/${personId}/interests`);
    return r.interests.map((i) => ({ id: str(i.interest_id), job_title: str(i.job_title), status: (str(i.status) as InterestRow["status"]) || "pending", at: str(i.created_at) }));
  },
  respond: (id: string, response: "accept" | "reject") => post<Rec>(`/api/interests/${id}/respond`, { response }),
  async matches(f: { job_id?: string; person_id?: string }): Promise<MatchRow[]> {
    const qs = new URLSearchParams(Object.entries(f).filter(([, v]) => v) as [string, string][]).toString();
    const r = await call<{ matches: Rec[] }>(`/api/matches${qs ? `?${qs}` : ""}`);
    return r.matches.map((m) => ({ id: str(m.match_id), name: str(m.candidate_name), job_title: str(m.job_title), person_id: str(m.person_id) }));
  },
};
