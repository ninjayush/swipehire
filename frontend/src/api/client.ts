// The ONLY module UI code talks to. Live mode never falls back to mocks.
import { USE_MOCKS, http, post } from "./http";
import { mock } from "./mock";
import { normalizeDeck, normalizePerson, normalizeRequirements } from "./mapping";
import type {
  CandidateDeck, Company, Interest, Job, JobRequirements, MatchItem, PersonRecord,
  RecruiterAction, ResumeUploadResult, ShortlistEntry,
} from "../types";

export { USE_MOCKS };

type Raw = Record<string, unknown>;
const normJob = (j: Raw): Job => ({
  job_id: String(j.job_id), company_id: String(j.company_id),
  title: String(j.title ?? (j.requirements as JobRequirements | undefined)?.title ?? "Untitled role"),
  status: String(j.status ?? "active"),
  requirements: normalizeRequirements((j.requirements ?? {}) as Partial<JobRequirements>),
  created_at: (j.created_at as string | null | undefined) ?? null,
});

export const api = {
  resolveCompany: (p: { company_name?: string; domain?: string }): Promise<Company> =>
    USE_MOCKS ? mock.resolveCompany(p) : post<Company>("/api/companies/resolve", p),

  createJob: async (company_id: string, input: { raw_jd?: string; requirements?: JobRequirements }): Promise<Job> => {
    if (USE_MOCKS) return mock.createJob(company_id, input);
    const body = input.requirements
      ? { company_id, input_type: "structured", requirements: input.requirements }
      : { company_id, input_type: "jd", raw_jd: input.raw_jd };
    return normJob(await post<Raw>("/api/jobs", body));
  },
  listJobs: async (company_id?: string): Promise<Job[]> => {
    if (USE_MOCKS) return mock.listJobs();
    const r = await http<{ jobs: Raw[] }>(`/api/jobs${company_id ? `?company_id=${encodeURIComponent(company_id)}` : ""}`);
    return r.jobs.map(normJob);
  },
  updateJob: async (id: string, patch: { status?: string; requirements?: JobRequirements }): Promise<Job> => {
    if (USE_MOCKS) return mock.updateJob(id, patch);
    return normJob(await http<Raw>(`/api/jobs/${id}`, { method: "PATCH", body: JSON.stringify(patch) }));
  },
  discover: async (id: string): Promise<CandidateDeck> =>
    USE_MOCKS ? mock.discover(id) : normalizeDeck(await post<Raw>(`/api/jobs/${id}/discover`)),
  getDeck: async (id: string): Promise<CandidateDeck> =>
    USE_MOCKS ? mock.getDeck(id) : normalizeDeck(await http<Raw>(`/api/jobs/${id}/deck`)),
  shortlist: async (id: string): Promise<ShortlistEntry[]> =>
    USE_MOCKS ? mock.shortlist(id) : (await http<{ shortlist: ShortlistEntry[] }>(`/api/jobs/${id}/shortlist`)).shortlist,
  recordAction: (job_id: string, person_id: string, action: RecruiterAction) =>
    USE_MOCKS ? mock.action(job_id, person_id, action) : post<Raw>(`/api/jobs/${job_id}/actions`, { person_id, action }),

  enrich: async (profile_url: string): Promise<PersonRecord> =>
    USE_MOCKS ? mock.enrich(profile_url) : normalizePerson((await post<{ person: PersonRecord }>("/api/candidates/enrich", { profile_url })).person),
  register: async (p: { person_id?: string; name?: string; email?: string; profile_url?: string; prefs: Record<string, unknown> }): Promise<PersonRecord> => {
    if (USE_MOCKS) return mock.register(p.person_id ?? `demo-new-${Date.now()}`, p.prefs, p.name);
    const r = await post<{ person: PersonRecord }>("/api/candidates/register", {
      person_id: p.person_id, name: p.name, email: p.email, profile_url: p.profile_url, candidate_preferences: p.prefs,
    });
    return normalizePerson(r.person);
  },
  uploadResume: (id: string, file: File): Promise<ResumeUploadResult> => {
    if (USE_MOCKS) return mock.uploadResume(id, file);
    const fd = new FormData();
    fd.append("file", file);
    return http<ResumeUploadResult>(`/api/candidates/${id}/resume`, { method: "POST", body: fd });
  },
  getCandidate: async (id: string): Promise<PersonRecord> =>
    USE_MOCKS ? mock.getCandidate(id) : normalizePerson((await http<{ person: PersonRecord }>(`/api/candidates/${id}`)).person),
  interests: async (person_id: string): Promise<Interest[]> =>
    USE_MOCKS ? mock.interests(person_id) : (await http<{ interests: Interest[] }>(`/api/candidates/${person_id}/interests`)).interests,
  respond: (interest_id: string, response: "accept" | "reject") =>
    USE_MOCKS ? mock.respond(interest_id, response) : post<Raw>(`/api/interests/${interest_id}/respond`, { response }),
  matches: async (f: { job_id?: string; person_id?: string } = {}): Promise<MatchItem[]> => {
    if (USE_MOCKS) return mock.matches(f);
    const qs = new URLSearchParams(Object.entries(f).filter(([, v]) => v) as [string, string][]).toString();
    return (await http<{ matches: MatchItem[] }>(`/api/matches${qs ? `?${qs}` : ""}`)).matches;
  },
};
