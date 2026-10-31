// Mirrors backend/app/database/schemas.py (source of truth). Do not rename fields.
export interface JobRequirements {
  title: string;
  seniority?: string | null;
  min_experience_years?: number | null;
  max_experience_years?: number | null;
  locations: string[];
  work_modes: string[];
  must_have_skills: string[];
  preferred_skills: string[];
  mandatory_qualifications: string[];
  preferred_qualifications: string[];
  required_fields: string[];
  dealbreakers: string[];
  unknown_or_needs_confirmation: string[];
  raw_jd?: string | null;
}

export type Rec = Record<string, unknown>;

export interface PersonRecord {
  person_id: string;
  crustdata_person_id?: number | null;
  profile_url?: string | null;
  origin: "registered" | "crustdata_sourced";
  membership_status: "registered" | "not_registered";
  name?: string | null;
  headline?: string | null;
  current_title?: string | null;
  current_company?: string | null;
  location?: string | null;
  skills: string[];
  experience_years?: number | null;
  employment_history: Rec[];
  education: Rec[];
  resume_highlights: Rec[];
  candidate_preferences: Rec;
  source_metadata: Rec[];
}

export interface EvidenceItem {
  criterion: string;
  evidence_text: string;
  source_type?: "resume" | "crustdata_profile" | "user_input";
  confidence_score?: number | null;
}

export interface CandidateEvaluation {
  person_id: string;
  eligible: boolean;
  exclusion_reasons: string[];
  fit_score?: number | null;
  component_scores: Record<string, number>;
  evidence_coverage?: number | null;
  fit_type?: "direct" | "adjacent" | null;
  match_explanation?: string | null;
  reasons: string[];
  rank?: number | null;
  evidence?: EvidenceItem[];
}

export interface DeckCard {
  person: PersonRecord;
  evaluation: CandidateEvaluation;
}

export interface CandidateDeck {
  job_id: string;
  match_run_id: string;
  status: "completed" | "failed" | "processing";
  total_candidates: number;
  direct_count: number;
  adjacent_count: number;
  excluded_count: number;
  cards: DeckCard[];
}

export interface Company {
  company_id: string;
  name: string;
  domain?: string | null;
  enriched: Rec;
  ambiguous_options: Rec[];
}

export interface Job {
  job_id: string;
  company_id: string;
  title: string;
  status: string;
  requirements: JobRequirements;
  created_at?: string | null;
}

export type RecruiterAction = "shortlist" | "pass" | "save";

export interface ShortlistEntry {
  person_id: string;
  name?: string | null;
  membership_status: "registered" | "not_registered";
  origin: string;
  action_created_at?: string | null;
}

export interface Interest {
  interest_id: string;
  job_id: string;
  job_title: string;
  status: string; // pending | accepted | rejected (backend-defined)
  created_at?: string | null;
}

export interface MatchItem {
  match_id: string;
  job_id: string;
  job_title: string;
  person_id: string;
  candidate_name: string;
  created_at?: string | null;
}

export interface ResumeUploadResult {
  parser_status?: string;
  parsed_data?: Rec | null;
  [k: string]: unknown;
}

export interface CandidatePrefs {
  target_role?: string;
  locations?: string[];
  work_mode?: string;
  availability?: string;
  salary_expectation?: string;
}
