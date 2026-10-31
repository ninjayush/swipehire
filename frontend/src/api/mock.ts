// DEMO DATA ONLY. Every person/company below is fictional. Used only when VITE_USE_MOCKS=true.
import type {
  CandidateDeck, Company, DeckCard, Interest, Job, JobRequirements, MatchItem, PersonRecord,
  RecruiterAction, ResumeUploadResult, ShortlistEntry,
} from "../types";
import { normalizeEvaluation, normalizePerson, normalizeRequirements } from "./mapping";

const wait = <T,>(v: T, ms = 350) => new Promise<T>((r) => setTimeout(() => r(v), ms));
const uid = () => Math.random().toString(36).slice(2, 10);

const src = (label: string) => [{ source: label, note: "Demo data — not a real person." }];

export const DEMO_PEOPLE: PersonRecord[] = [
  normalizePerson({
    person_id: "demo-asha", origin: "registered", membership_status: "registered",
    name: "Asha Verma (demo)", headline: "Backend engineer building reliable data platforms",
    current_title: "Senior Backend Engineer", current_company: "Northwind Labs (demo)", location: "Bengaluru, India",
    skills: ["Python", "FastAPI", "PostgreSQL", "AWS", "Kafka"], experience_years: 7,
    employment_history: [
      { title: "Senior Backend Engineer", company: "Northwind Labs (demo)", start: "2021", end: "Present", summary: "Led a 5-person team shipping an event pipeline handling 40M events/day." },
      { title: "Backend Engineer", company: "Parcel Co (demo)", start: "2018", end: "2021", summary: "Built REST services and cut p95 latency by 38%." },
    ],
    education: [{ school: "Demo Institute of Technology", degree: "B.Tech, Computer Science", year: "2018" }],
    resume_highlights: [
      { label: "A project I'm proud of", text: "Rebuilt the ingestion service on Kafka, removing a nightly batch window." },
      { label: "Impact I've delivered", text: "Reduced infrastructure spend by 22% through query and index tuning." },
    ],
    candidate_preferences: { target_role: "Staff Backend Engineer", work_mode: "hybrid", availability: "30 days notice" },
    source_metadata: src("resume"),
  }),
  normalizePerson({
    person_id: "demo-marcus", origin: "registered", membership_status: "registered",
    name: "Marcus Lee (demo)", headline: "Data engineer moving toward application backends",
    current_title: "Data Platform Engineer", current_company: "Lumen Analytics (demo)", location: "Singapore",
    skills: ["Python", "SQL", "Airflow", "Docker", "Go"], experience_years: 5,
    employment_history: [{ title: "Data Platform Engineer", company: "Lumen Analytics (demo)", start: "2020", end: "Present", summary: "Owns internal APIs and orchestration services used by 12 teams." }],
    education: [{ school: "Demo National University", degree: "B.Sc, Information Systems", year: "2019" }],
    resume_highlights: [{ label: "A problem I've solved", text: "Replaced brittle cron jobs with a typed service layer and retries." }],
    candidate_preferences: {},
    source_metadata: src("resume"),
  }),
  normalizePerson({
    person_id: "demo-priya", origin: "crustdata_sourced", membership_status: "not_registered",
    name: "Priya Nair (demo)", headline: "Platform engineer — cloud and services",
    current_title: "Platform Engineer", current_company: "Orbit Systems (demo)", location: "Hyderabad, India",
    skills: ["Python", "FastAPI", "Kubernetes", "AWS"], experience_years: 6,
    employment_history: [{ title: "Platform Engineer", company: "Orbit Systems (demo)", start: "2019", end: "Present" }],
    education: [], resume_highlights: [], candidate_preferences: {},
    source_metadata: src("crustdata_profile"),
  }),
  normalizePerson({
    person_id: "demo-tomas", origin: "registered", membership_status: "registered",
    name: "Tomás Rivera (demo)", headline: "Full-stack developer",
    current_title: "Software Engineer", current_company: "Brightpath (demo)", location: null,
    skills: ["Python", "Django", "React"], experience_years: null,
    employment_history: [], education: [], resume_highlights: [], candidate_preferences: {},
    source_metadata: src("user_input"),
  }),
];

const EVALS: Record<string, ReturnType<typeof normalizeEvaluation>> = {
  "demo-asha": normalizeEvaluation({ fit_score: 91, fit_type: "direct", rank: 1, evidence_coverage: 0.92,
    component_scores: { skills: 94, experience: 90, role_domain: 92, seniority: 88, contextual: 80 },
    match_explanation: "Seven years of Python and FastAPI services, including a Kafka pipeline at 40M events/day, matches every must-have skill.",
    reasons: ["All must-have skills evidenced in resume", "Seniority aligns with the role", "Location matches requirement"] }, "demo-asha"),
  "demo-marcus": normalizeEvaluation({ fit_score: 74, fit_type: "adjacent", rank: 2, evidence_coverage: 0.7,
    component_scores: { skills: 72, experience: 70, role_domain: 66, seniority: 78, contextual: 70 },
    match_explanation: "Title is data-platform rather than backend, but he owns production Python APIs and meets every must-have. Misses the preferred AWS skill.",
    reasons: ["Passes all mandatory criteria", "Transferable API ownership experience", "Preferred skill missing: AWS"] }, "demo-marcus"),
  "demo-priya": normalizeEvaluation({ fit_score: 82, fit_type: "direct", rank: 3, evidence_coverage: 0.64,
    component_scores: { skills: 85, experience: 80, role_domain: 82, seniority: 80, contextual: 70 },
    match_explanation: "Python, FastAPI and AWS appear on her public profile; work history is as listed by the source and not independently verified.",
    reasons: ["Must-have skills listed on profile", "Not on SwipeHire — internal shortlist only"] }, "demo-priya"),
  "demo-tomas": normalizeEvaluation({ fit_score: 63, fit_type: "adjacent", rank: 4, evidence_coverage: 0.4,
    component_scores: { skills: 60, experience: 0, role_domain: 70, seniority: 0, contextual: 60 },
    match_explanation: "Python and web skills match; experience length and location are not provided and need confirmation.",
    reasons: ["Experience years unknown", "Location unknown"] }, "demo-tomas"),
};

const REQ: JobRequirements = normalizeRequirements({
  title: "Senior Backend Engineer", seniority: "Senior", min_experience_years: 5,
  locations: ["Bengaluru", "Remote India"], work_modes: ["hybrid", "remote"],
  must_have_skills: ["Python", "FastAPI", "SQL"], preferred_skills: ["AWS", "Kafka"],
  mandatory_qualifications: [], preferred_qualifications: ["Led a small team"],
  required_fields: [], dealbreakers: [], unknown_or_needs_confirmation: ["Is relocation acceptable?"],
});

const db = {
  companies: [] as Company[],
  jobs: [{ job_id: "demo-job-1", company_id: "demo-co", title: REQ.title, status: "active", requirements: REQ, created_at: new Date().toISOString() }] as Job[],
  decks: {} as Record<string, boolean>,
  actions: [] as { job_id: string; person_id: string; action: RecruiterAction; at: string }[],
  interests: [] as (Interest & { person_id: string })[],
  matches: [] as MatchItem[],
  people: [...DEMO_PEOPLE] as PersonRecord[],
};

export const mock = {
  async resolveCompany(p: { company_name?: string; domain?: string }): Promise<Company> {
    const name = p.company_name || p.domain || "Demo Co";
    const c: Company = {
      company_id: "demo-co", name, domain: p.domain ?? null,
      enriched: { location: "Demo City", summary: "Demo company record — not enriched by Crustdata." },
      ambiguous_options: [
        { company_id: "demo-co", name, domain: p.domain ?? `${name.toLowerCase().replace(/\W+/g, "")}.com`, location: "Demo City" },
        { company_id: "demo-co-2", name: `${name} Labs`, domain: `${name.toLowerCase().replace(/\W+/g, "")}labs.io`, location: "Remote" },
      ],
    };
    db.companies = [c];
    return wait(c);
  },
  async createJob(company_id: string, input: { raw_jd?: string; requirements?: JobRequirements }): Promise<Job> {
    const requirements = input.requirements
      ? normalizeRequirements(input.requirements)
      : normalizeRequirements({
          title: (input.raw_jd ?? "").split("\n").find((l) => l.trim())?.trim().slice(0, 80) || "New role",
          must_have_skills: ["Python"], raw_jd: input.raw_jd,
          unknown_or_needs_confirmation: ["Demo parser only extracted a title — add real requirements below."],
        });
    const job: Job = { job_id: uid(), company_id, title: requirements.title, status: input.requirements ? "active" : "needs_confirmation", requirements, created_at: new Date().toISOString() };
    db.jobs.unshift(job);
    return wait(job);
  },
  async listJobs(): Promise<Job[]> { return wait([...db.jobs], 200); },
  async updateJob(id: string, patch: { status?: string; requirements?: JobRequirements }): Promise<Job> {
    const j = db.jobs.find((x) => x.job_id === id);
    if (!j) throw new Error("Job not found");
    if (patch.requirements) { j.requirements = patch.requirements; j.title = patch.requirements.title; }
    if (patch.status) j.status = patch.status;
    return wait({ ...j }, 200);
  },
  async discover(job_id: string): Promise<CandidateDeck> {
    db.decks[job_id] = true;
    return wait(buildDeck(job_id), 1400);
  },
  async getDeck(job_id: string): Promise<CandidateDeck> {
    if (!db.decks[job_id]) throw Object.assign(new Error("No candidate deck found. Run discovery first."), { kind: "not_found" });
    return wait(buildDeck(job_id));
  },
  async shortlist(job_id: string): Promise<ShortlistEntry[]> {
    return wait(db.actions.filter((a) => a.job_id === job_id && a.action === "shortlist").map((a) => entry(a.person_id, a.at)), 200);
  },
  async saved(): Promise<{ job_id: string; person_id: string; at: string }[]> {
    return wait(db.actions.filter((a) => a.action === "save"), 200);
  },
  async action(job_id: string, person_id: string, action: RecruiterAction) {
    const p = db.people.find((x) => x.person_id === person_id);
    db.actions = db.actions.filter((a) => !(a.job_id === job_id && a.person_id === person_id));
    db.actions.push({ job_id, person_id, action, at: new Date().toISOString() });
    // Only registered members receive an interest. Non-members: internal shortlist only.
    if (action === "shortlist" && p?.membership_status === "registered" && !db.interests.some((i) => i.job_id === job_id && i.person_id === person_id)) {
      const job = db.jobs.find((j) => j.job_id === job_id);
      db.interests.push({ interest_id: uid(), job_id, job_title: job?.title ?? "Role", status: "pending", created_at: new Date().toISOString(), person_id });
    }
    return wait({ status: "recorded", action }, 150);
  },
  async enrich(profile_url: string): Promise<PersonRecord> {
    const p = normalizePerson({
      person_id: `demo-new-${uid()}`, profile_url, origin: "registered", membership_status: "registered",
      name: "Demo Candidate", headline: "Product-minded engineer", current_title: "Software Engineer",
      current_company: "Demo Co", location: "Demo City", skills: ["TypeScript", "Python"], experience_years: 4,
      source_metadata: src("crustdata_profile"),
    });
    db.people.push(p);
    return wait(p, 900);
  },
  async register(person_id: string, prefs: Record<string, unknown>, name?: string): Promise<PersonRecord> {
    let p = db.people.find((x) => x.person_id === person_id);
    if (!p) { p = normalizePerson({ person_id, name: name ?? "Demo Candidate", membership_status: "registered", origin: "registered" }); db.people.push(p); }
    p.membership_status = "registered"; p.origin = "registered"; p.candidate_preferences = prefs; if (name) p.name = name;
    return wait({ ...p }, 300);
  },
  async uploadResume(_id: string, file: File): Promise<ResumeUploadResult> {
    return wait({ parser_status: "mock", parsed_data: { file: file.name, skills: ["Python", "SQL"], highlights: ["Demo parse — no real resume content was read."] } }, 900);
  },
  async getCandidate(id: string): Promise<PersonRecord> {
    const p = db.people.find((x) => x.person_id === id);
    if (!p) throw Object.assign(new Error("Candidate not found"), { kind: "not_found" });
    return wait({ ...p }, 200);
  },
  async interests(person_id: string): Promise<Interest[]> {
    return wait(db.interests.filter((i) => i.person_id === person_id), 200);
  },
  async respond(interest_id: string, response: "accept" | "reject") {
    const i = db.interests.find((x) => x.interest_id === interest_id);
    if (!i) throw new Error("Interest not found");
    i.status = response === "accept" ? "accepted" : "rejected";
    if (response === "accept" && !db.matches.some((m) => m.job_id === i.job_id && m.person_id === i.person_id)) {
      const p = db.people.find((x) => x.person_id === i.person_id);
      db.matches.push({ match_id: uid(), job_id: i.job_id, job_title: i.job_title, person_id: i.person_id, candidate_name: p?.name ?? "Candidate", created_at: new Date().toISOString() });
    }
    return wait({ status: i.status }, 250);
  },
  async matches(f: { job_id?: string; person_id?: string }): Promise<MatchItem[]> {
    return wait(db.matches.filter((m) => (!f.job_id || m.job_id === f.job_id) && (!f.person_id || m.person_id === f.person_id)), 200);
  },
  allInterests: () => db.interests,
};

function entry(person_id: string, at: string): ShortlistEntry {
  const p = db.people.find((x) => x.person_id === person_id);
  return { person_id, name: p?.name, membership_status: p?.membership_status ?? "not_registered", origin: p?.origin ?? "crustdata_sourced", action_created_at: at };
}

function buildDeck(job_id: string): CandidateDeck {
  const cards: DeckCard[] = DEMO_PEOPLE.map((person) => ({ person, evaluation: EVALS[person.person_id] }));
  return {
    job_id, match_run_id: "demo-run", status: "completed", total_candidates: 7,
    direct_count: cards.filter((c) => c.evaluation.fit_type === "direct").length,
    adjacent_count: cards.filter((c) => c.evaluation.fit_type === "adjacent").length,
    excluded_count: 3, cards,
  };
}
