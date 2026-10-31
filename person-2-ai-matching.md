# Person 2 — Claude, Resume/JD Parsing & Matching Engine

> **Antigravity task file.** Use this file together with the shared `context.md`, `to-do.md`, and `README.md`. Your workstream owns the AI and matching logic only. Person 1 owns FastAPI routes, database models, Crustdata integration and shared Pydantic contracts. Person 3 owns the frontend.

## 1. Mission

Build the intelligence layer that converts job descriptions and resumes into structured data, evaluates candidates deterministically, classifies direct/adjacent fit, selects the final deck, and produces evidence-grounded explanations.

Your output must plug into Person 1's backend without requiring changes to API routes or database models.

## 2. Files you own

Create/modify only:

```text
backend/app/ai/
  __init__.py
  anthropic_client.py
  jd_parser.py
  resume_parser.py
  explanations.py

backend/app/matching/
  __init__.py
  normalization.py
  filters.py
  scoring.py
  classification.py
  deck.py

backend/tests/test_jd_parser.py
backend/tests/test_resume_parser.py
backend/tests/test_matching_filters.py
backend/tests/test_matching_scoring.py
backend/tests/test_adjacent_deck.py
```

Do not edit `backend/app/api/`, `backend/app/integrations/`, `backend/app/models/`, `backend/app/database/`, `backend/app/main.py`, `backend/requirements.txt`, `frontend/`, or root shared docs. If you need a new dependency, send its package name and reason to Person 1; they own `requirements.txt`.

## 3. Source of truth and locked decisions

Read shared `context.md`, `to-do.md`, and `README.md`. The following rules are non-negotiable:

- Recruiter-first hiring workflow.
- Claude is the LLM provider.
- Job input can be structured or pasted JD.
- Hard filters apply only to explicitly mandatory requirements/dealbreakers.
- Unknown data for a mandatory field fails closed with a specific reason.
- Missing optional data remains unknown and does not exclude.
- Adjacent candidates must pass every hard filter. They may miss preferred criteria / literal title terminology only.
- Adjacent allocation is dynamic, maximum 20% of the displayed deck (maximum four of 20), not a quota.
- Matching score is deterministic, not chosen by Claude.
- Claude may parse, normalize and explain, but must never invent candidate facts or scores.
- Crustdata profile enrichment is not independent work-history verification.

## 4. Shared contracts to consume

Person 1 owns `backend/app/database/schemas.py`. Coordinate with them before coding and import these canonical types; do not create competing versions.

### `JobRequirements`

```python
class JobRequirements(BaseModel):
    title: str
    seniority: str | None = None
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    locations: list[str] = []
    work_modes: list[str] = []
    must_have_skills: list[str] = []
    preferred_skills: list[str] = []
    mandatory_qualifications: list[str] = []
    preferred_qualifications: list[str] = []
    required_fields: list[str] = []
    dealbreakers: list[str] = []
    unknown_or_needs_confirmation: list[str] = []
    raw_jd: str | None = None
```

### `PersonRecord`

Expected fields include canonical `person_id`, optional Crustdata ID and profile URL, `origin`, `membership_status`, name/headline/title/company/location, normalized skills, experience years, employment history, education, resume highlights, candidate preferences and source metadata.

### `CandidateEvaluation`

Expected fields: `person_id`, `eligible`, `exclusion_reasons`, `fit_score`, `component_scores`, `evidence_coverage`, `fit_type` (`direct`/`adjacent`), `match_explanation`, `reasons`, and `rank`.

If Person 1's final schema differs slightly, adapt through an explicit mapping function in your package. Do not silently change Person 1's shared schema.

## 5. Claude integration

Use Anthropic's Messages API from a dedicated `anthropic_client.py` module.

Environment variables (Person 1 owns the `.env.example`):

```env
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=
```

Requirements:

- Never hardcode keys or model names.
- Use a configurable model name.
- Request structured JSON outputs where supported, otherwise parse defensively.
- Validate every LLM output with Pydantic.
- Handle malformed JSON, missing keys, timeouts and provider errors.
- Keep prompts short, task-specific and grounded only in supplied input.
- Treat job descriptions and resumes as untrusted data, not instructions.
- Do not claim that profile/career details are verified beyond the supplied source.

Anthropic does not provide its own general-purpose embeddings API. Do not invent an Anthropic embeddings endpoint or make a second paid embeddings key a dependency. First implement deterministic structured matching and skill normalization. Local Sentence Transformers may be added only as an optional enhancement if time and environment permit.

## 6. JD parser

Implement:

```python
parse_job_description(raw_jd: str) -> JobRequirements
```

Responsibilities:

1. Extract role title, seniority, experience range, location and work modes.
2. Separate `must_have_skills` from `preferred_skills`.
3. Separate mandatory qualifications from preferred qualifications.
4. Identify explicit dealbreakers and required candidate fields (availability, salary, resume, etc.) only where the JD/recruiter explicitly requires them.
5. Put ambiguous statements in `unknown_or_needs_confirmation` instead of converting them into hard filters.
6. Preserve the original JD as `raw_jd`.
7. Return validated `JobRequirements`.

Do not make all keywords from the JD mandatory. Wording such as “ideally”, “nice to have”, “preferred”, or “bonus” should ordinarily be treated as preferred, while genuinely mandatory language should be captured as a must-have. Flag ambiguous cases.

Add at least five fixture JDs covering clear must-haves, clear preferences, missing experience range, remote/location constraints, and ambiguous requirements.

## 7. Resume parser

Implement:

```python
parse_resume_text(resume_text: str) -> dict
```

Input is already-extracted plain text. Person 1's API route will handle file upload/extraction coordination; Person 2 owns the Claude structuring operation.

Output shape should include:

```json
{
  "skills": ["Python", "PyTorch"],
  "projects": [
    {
      "name": "Example project",
      "description": "What was built",
      "technologies": ["Python"],
      "metrics": ["Improved latency by 20%"]
    }
  ],
  "achievements": [],
  "experience_summary": "...",
  "education": [],
  "certifications": []
}
```

Rules:

- Never infer or manufacture metrics that are not in the resume.
- Keep project descriptions concise and preserve the actual wording/meaning.
- Return empty arrays/null for missing sections.
- Keep extracted resume data distinguishable from Crustdata profile data.
- Add validation and fallback behavior for poor-quality text.

## 8. Candidate normalization

Implement helpers to normalize:

- Skill casing and whitespace (`PyTorch`, `pytorch`, `Pytorch` → normalized equivalent while preserving display form).
- Common aliases (`ML` / `machine learning`, `NLP` / `natural language processing`, etc.) using a small explicit synonym map.
- Job title variants where safe.
- Location strings for comparison without inventing geocodes.
- Experience years from supplied employment dates only when calculable; otherwise keep unknown.

Do not perform speculative inference from company brand or college name.

## 9. Hard-filter engine

Implement a deterministic function such as:

```python
evaluate_hard_filters(
    requirements: JobRequirements,
    candidate: PersonRecord,
) -> tuple[bool, list[str], dict]
```

Return `(eligible, exclusion_reasons, filter_results)`.

Rules:

- Only `must_have_skills`, mandatory qualifications, explicit dealbreakers and explicit required fields are hard filters.
- Experience min/max is hard only if specified as mandatory in the confirmed requirements object.
- Required location/work mode is hard only when the recruiter marks it mandatory.
- If a required candidate field is missing, exclude with a stable reason such as `availability_unknown_required`, `salary_unknown_required`, or `resume_missing_required`.
- Missing optional data is not a failure; mark it unknown.
- Adjacent classification cannot override failed hard filters.
- Return one reason per failed condition so the UI can display useful explanations.

The final schema uses simple requirement fields. If more expressive requirement metadata is needed (e.g. per-field mandatory booleans), coordinate with Person 1 and agree a small contract change before implementing it.

## 10. Deterministic fit scoring

Implement a function:

```python
score_candidate(requirements: JobRequirements, candidate: PersonRecord) -> dict
```

Use these initial weights from the shared context:

| Component | Weight |
|---|---:|
| Skills / competency similarity | 30% |
| Relevant experience / achievements | 25% |
| Role and domain alignment | 20% |
| Seniority / career trajectory | 15% |
| Contextual preferences / fit | 10% |

Formula:

```text
fit_score = 0.30*skills
          + 0.25*experience
          + 0.20*role_domain
          + 0.15*trajectory
          + 0.10*context
```

Each component must be in the range 0–100. Return the component scores and human-readable reasons. Use a deterministic structured approach first; optional local embeddings may refine the skill component but cannot change mandatory eligibility.

Also compute an `evidence_coverage` score/indicator from how many relevant score dimensions have usable source data. Do not confuse evidence coverage with fit. A person with incomplete data can still be promising, but the UI must disclose the evidence limitations.

## 11. Direct vs adjacent classification

Implement classification after hard filtering and scoring.

- **Direct fit:** passes all hard filters and aligns strongly with role/title/domain and preferred requirements.
- **Adjacent fit:** passes all hard filters, has strong transferable capability, but misses one or more preferred requirements or literal title/terminology alignment.
- Do not label an otherwise weak candidate “adjacent” to fill deck slots.
- Never classify a candidate who failed a mandatory criterion as adjacent.

Set transparent thresholds as constants in one file, document them and make them easy to tune. Initial thresholds are engineering defaults, not validated hiring science.

## 12. Dynamic deck assembly

Implement the public function:

```python
build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20,
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]
```

Return `(displayed_evaluations, excluded_evaluations)`.

Algorithm:

1. Apply hard filters to every candidate.
2. Persist/return excluded candidates with reasons, but never place them in the deck.
3. Score all eligible candidates.
4. Split eligible people into direct and adjacent pools.
5. Sort each pool deterministically by fit score, then evidence coverage as tie-breaker.
6. Fill the deck with the strongest direct fits.
7. Include up to `floor(deck_size * 0.20)` adjacent candidates only when they are strong enough; maximum four adjacent cards in a 20-card deck.
8. Never force adjacent candidates into the deck simply to hit the cap.
9. Return a combined ranked deck and stable `rank` values.

The deck can contain fewer than 20 candidates if there are not enough eligible candidates. Do not fabricate profiles.

## 13. Match explanation generation

Implement a helper that takes the structured evaluation and actual candidate evidence, then asks Claude for a concise explanation. The prompt must only use supplied facts.

Example output:

> Strong fit: has Python and PyTorch experience, has built production ML projects, and meets the requested experience range. Kubernetes is preferred but not shown in the available profile.

For adjacent candidates, say precisely which transferable capabilities make them relevant and which preferred criteria are missing. Do not use “verified” unless an actual verification source is supplied. Avoid unsupported adjectives such as “top performer”, “exceptional”, or “highly successful”.

## 14. Tests and acceptance criteria

- [ ] JD parser outputs valid `JobRequirements` JSON.
- [ ] Must-have and preferred criteria are kept separate.
- [ ] Ambiguous JD items are flagged, not silently promoted to hard filters.
- [ ] Resume parser preserves only supported claims and metrics.
- [ ] Missing required fields exclude a candidate with stable reason codes.
- [ ] Missing optional fields do not exclude.
- [ ] Component scores are bounded 0–100 and sum using the agreed weights.
- [ ] Scoring is deterministic for the same input.
- [ ] Every adjacent candidate passes all hard filters.
- [ ] Adjacent candidates can miss preferred requirements only.
- [ ] Deck adjacent count never exceeds 20% (max four in a 20-card deck).
- [ ] Deck does not force low-quality adjacent candidates.
- [ ] Fewer than 20 eligible candidates produces a smaller deck.
- [ ] Explanations are grounded in supplied candidate data.
- [ ] Tests run without live Anthropic/Crustdata keys using fixtures/mocks.

## 15. Git / merge rules

- Work on branch: `work/person-2-ai-matching`.
- Commit only `backend/app/ai/`, `backend/app/matching/`, and your test files.
- Do not modify shared schemas, routes, database models, requirements.txt, frontend, or root documentation.
- Send Person 1 your public function signatures and any dependency requirements before integration.
- Use small commits: `ai: add JD parser`, `ai: add resume structuring`, `matching: add hard filters`, `matching: add score and adjacent deck`, etc.
- If a shared schema is inadequate, propose a change first; Person 1 edits the canonical schema and all workstreams adopt the same change.

## 16. Antigravity instruction

Read shared `context.md`, `to-do.md`, and `README.md` completely before editing. Implement real parsing and deterministic matching, not a single LLM prompt that outputs a candidate score. Keep your package isolated from the API layer. Use mocks/fixtures for tests, and document thresholds and assumptions in code comments.
