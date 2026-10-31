// DEMO DATA ONLY — fictional people. Mirrors backend PersonRecord / CandidateEvaluation fields.
export interface Person {
  person_id: string; name: string; headline: string; current_title: string; current_company: string;
  location: string | null; skills: string[]; experience_years: number | null; member: boolean;
  history: { title: string; company: string; years: string; note?: string }[];
  education: string[];
  prompts: { label: string; text: string }[];
}
export interface Evaluation { fit_score: number; fit_type: "direct" | "adjacent"; explanation: string; components: Record<string, number>; coverage: number }
export interface DeckCard { person: Person; ev: Evaluation }

export const DECK: DeckCard[] = [
  { person: { person_id: "demo-asha", name: "Asha Verma", headline: "Backend engineer building reliable data platforms", current_title: "Senior Backend Engineer", current_company: "Northwind Labs", location: "Bengaluru", skills: ["Python", "FastAPI", "PostgreSQL", "AWS", "Kafka"], experience_years: 7, member: true,
      history: [{ title: "Senior Backend Engineer", company: "Northwind Labs", years: "2021 – Now", note: "Led a 5-person team on a 40M events/day pipeline." }, { title: "Backend Engineer", company: "Parcel Co", years: "2018 – 2021", note: "Cut p95 latency by 38%." }],
      education: ["B.Tech Computer Science, Demo Institute of Technology"],
      prompts: [{ label: "A project I'm proud of", text: "Rebuilt ingestion on Kafka and retired a nightly batch window." }, { label: "Impact I've delivered", text: "Cut infrastructure spend 22% through query and index tuning." }, { label: "What I'm looking for next", text: "Staff-level ownership of a platform team, hybrid." }] },
    ev: { fit_score: 91, fit_type: "direct", explanation: "Seven years of Python and FastAPI, including a Kafka pipeline at 40M events/day — every must-have is evidenced.", components: { Skills: 94, Experience: 90, "Role & domain": 92, Seniority: 88, Context: 80 }, coverage: 0.92 } },
  { person: { person_id: "demo-marcus", name: "Marcus Lee", headline: "Data engineer moving toward application backends", current_title: "Data Platform Engineer", current_company: "Lumen Analytics", location: "Singapore", skills: ["Python", "SQL", "Airflow", "Docker", "Go"], experience_years: 5, member: true,
      history: [{ title: "Data Platform Engineer", company: "Lumen Analytics", years: "2020 – Now", note: "Owns internal APIs used by 12 teams." }],
      education: ["B.Sc Information Systems, Demo National University"],
      prompts: [{ label: "A problem I've solved", text: "Replaced brittle cron jobs with a typed service layer and retries." }] },
    ev: { fit_score: 74, fit_type: "adjacent", explanation: "Title is data-platform, not backend, but he owns production Python APIs and meets every must-have. Misses preferred AWS.", components: { Skills: 72, Experience: 70, "Role & domain": 66, Seniority: 78, Context: 70 }, coverage: 0.7 } },
  { person: { person_id: "demo-priya", name: "Priya Nair", headline: "Platform engineer — cloud and services", current_title: "Platform Engineer", current_company: "Orbit Systems", location: "Hyderabad", skills: ["Python", "FastAPI", "Kubernetes", "AWS"], experience_years: 6, member: false,
      history: [{ title: "Platform Engineer", company: "Orbit Systems", years: "2019 – Now" }], education: [], prompts: [] },
    ev: { fit_score: 82, fit_type: "direct", explanation: "Python, FastAPI and AWS appear on her public profile; history is source-listed, not independently verified.", components: { Skills: 85, Experience: 80, "Role & domain": 82, Seniority: 80, Context: 70 }, coverage: 0.64 } },
  { person: { person_id: "demo-tomas", name: "Tomás Rivera", headline: "Full-stack developer", current_title: "Software Engineer", current_company: "Brightpath", location: null, skills: ["Python", "Django", "React"], experience_years: null, member: true,
      history: [], education: [], prompts: [] },
    ev: { fit_score: 63, fit_type: "adjacent", explanation: "Python and web skills match; experience length and location aren't provided and need confirmation.", components: { Skills: 60, "Role & domain": 70, Context: 60 }, coverage: 0.4 } },
];
export const DEMO_CANDIDATE_ID = "demo-asha";
export const JOB_TITLE = "Senior Backend Engineer";
