import type { CandidateDeck, CandidateEvaluation, DeckCard, JobRequirements, PersonRecord } from "../types";

const arr = <T,>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : []);

export function normalizePerson(p: Partial<PersonRecord> & { person_id: string }): PersonRecord {
  const registered = p.membership_status === "registered";
  return {
    person_id: p.person_id,
    crustdata_person_id: p.crustdata_person_id ?? null,
    profile_url: p.profile_url ?? null,
    origin: p.origin ?? (registered ? "registered" : "crustdata_sourced"),
    membership_status: p.membership_status ?? "not_registered",
    name: p.name ?? null,
    headline: p.headline ?? null,
    current_title: p.current_title ?? null,
    current_company: p.current_company ?? null,
    location: p.location ?? null,
    skills: arr<string>(p.skills),
    experience_years: p.experience_years ?? null,
    employment_history: arr(p.employment_history),
    education: arr(p.education),
    resume_highlights: arr(p.resume_highlights),
    candidate_preferences: p.candidate_preferences ?? {},
    source_metadata: arr(p.source_metadata),
  };
}

export function normalizeEvaluation(e: Partial<CandidateEvaluation> | undefined, personId: string): CandidateEvaluation {
  return {
    person_id: e?.person_id ?? personId,
    eligible: e?.eligible ?? true,
    exclusion_reasons: arr<string>(e?.exclusion_reasons),
    fit_score: e?.fit_score ?? null,
    component_scores: e?.component_scores ?? {},
    evidence_coverage: e?.evidence_coverage ?? null,
    fit_type: e?.fit_type ?? null,
    match_explanation: e?.match_explanation ?? null,
    reasons: arr<string>(e?.reasons),
    rank: e?.rank ?? null,
    evidence: arr(e?.evidence),
  };
}

/** Backend `cards` is list[dict]. Current shape is {person, evaluation}; a flat merged dict is tolerated. */
export function normalizeDeck(raw: Record<string, unknown>): CandidateDeck {
  const cards: DeckCard[] = arr<Record<string, unknown>>(raw.cards).map((c) => {
    const personRaw = (c.person ?? c) as Partial<PersonRecord> & { person_id: string };
    const person = normalizePerson(personRaw);
    const evaluation = normalizeEvaluation((c.evaluation ?? c) as Partial<CandidateEvaluation>, person.person_id);
    return { person, evaluation };
  });
  return {
    job_id: String(raw.job_id),
    match_run_id: String(raw.match_run_id),
    status: (raw.status as CandidateDeck["status"]) ?? "completed",
    total_candidates: Number(raw.total_candidates ?? cards.length),
    direct_count: Number(raw.direct_count ?? 0),
    adjacent_count: Number(raw.adjacent_count ?? 0),
    excluded_count: Number(raw.excluded_count ?? 0),
    cards,
  };
}

export function normalizeRequirements(r: Partial<JobRequirements>): JobRequirements {
  return {
    title: r.title ?? "Untitled role",
    seniority: r.seniority ?? null,
    min_experience_years: r.min_experience_years ?? null,
    max_experience_years: r.max_experience_years ?? null,
    locations: arr<string>(r.locations),
    work_modes: arr<string>(r.work_modes),
    must_have_skills: arr<string>(r.must_have_skills),
    preferred_skills: arr<string>(r.preferred_skills),
    mandatory_qualifications: arr<string>(r.mandatory_qualifications),
    preferred_qualifications: arr<string>(r.preferred_qualifications),
    required_fields: arr<string>(r.required_fields),
    dealbreakers: arr<string>(r.dealbreakers),
    unknown_or_needs_confirmation: arr<string>(r.unknown_or_needs_confirmation),
    raw_jd: r.raw_jd ?? null,
  };
}
