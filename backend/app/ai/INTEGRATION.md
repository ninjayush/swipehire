# Person 2 — AI & Matching Integration Note & Final Handoff

This document is the definitive integration specification and handoff guide for Person 2's workstream (`backend/app/ai/` and `backend/app/matching/`). Person 1 (Backend/Orchestration) and Person 3 (Frontend) can use this guide to integrate all parsing, scoring, deck assembly, and explanation services.

---

## 1. Ownership & Package Boundary

- **Person 2 owns:**
  - `backend/app/ai/`
  - `backend/app/matching/`
  - `backend/tests/ai/`
  - `backend/tests/matching/`
  - `backend/app/ai/INTEGRATION.md`
- **Person 1 owns:**
  - `backend/app/api/` (routes)
  - `backend/app/integrations/` (Crustdata adapter)
  - `backend/app/models/` (database models)
  - `backend/app/database/schemas.py` (canonical shared Pydantic contracts)
  - Backend orchestration, persistence, `config.py`, and `requirements.txt`
- **Person 3 owns:**
  - `frontend/`

---

## 2. Public API Signatures & Calling Convention

All three public functions are strictly **synchronous** and can be called directly without asynchronous coroutine wrappers or event loops:

```python
# 1. Job Description Parsing (Claude Messages API with untrusted guardrails)
from app.ai import parse_job_description
# or: from app.ai.jd_parser import parse_job_description
def parse_job_description(raw_jd: str) -> JobRequirements: ...

# 2. Resume Plain-Text Structuring (Claude with provenance tags)
from app.ai import parse_resume_text
# or: from app.ai.resume_parser import parse_resume_text
def parse_resume_text(resume_text: str) -> dict[str, Any]: ...

# 3. Dynamic Candidate Deck Assembly (Pure deterministic matching + explanations)
from app.matching import build_candidate_deck
# or: from app.matching.deck import build_candidate_deck
def build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20,
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]: ...
```

---

## 3. Dependency & Configuration Requirements for Person 1

### Required Dependency
Add the following to `backend/requirements.txt`:
```text
anthropic>=0.40.0
```

### Environment Variables
| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (for AI parsing) | *None* | Authentication key for Claude Messages API. |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-20241022` | Configurable model for JD/resume parsing and explanation polishing. |
| `ANTHROPIC_TIMEOUT` | No | `30.0` | Finite timeout (seconds) for synchronous API requests. |

*Note: If `ANTHROPIC_API_KEY` is not configured, `build_candidate_deck` will still function 100% deterministically using the built-in evidence-grounded template fallback.*

---

## 4. Job Description Parser Behavior (`parse_job_description`)

- **Strict Categorization**:
  - `must_have_skills`: Only explicitly compulsory, required, or non-negotiable skills.
  - `preferred_skills`: Nice-to-have, bonus, or preferred skills. Any accidental overlap with must-have skills is automatically pruned from preferred.
  - `mandatory_qualifications`: Compulsory degrees or certifications.
  - `preferred_qualifications`: Desired or bonus credentials.
  - `dealbreakers`: Explicit geographic, authorization, or work mode mandates.
  - `required_fields`: Candidate profile fields explicitly demanded for eligibility by the JD (e.g., notice period, portfolio).
- **Ambiguity Surfacing**:
  - Vague soft skills ("strong communication", "rockstar attitude") and contradictory requirements ("junior title with 8 years experience") are placed in `unknown_or_needs_confirmation`. They are **never** silently promoted to hard filters.
- **Experience Bounds**:
  - Extracted only from explicit numeric statements ("5+ years" $\to$ min 5.0; "3–5 years" $\to$ min 3.0, max 5.0). Vague phrases like "experienced" leave bounds as `None`.
- **Exact Raw Preservation**:
  - `JobRequirements.raw_jd` always preserves the exact input string.

---

## 5. Resume Parser Output Contract & Schema Mapping (`parse_resume_text`)

Returns a pure JSON-serializable Python dictionary with the following shape:
```json
{
  "skills": ["Go", "Python", "FastAPI", "Docker"],
  "projects": [
    {
      "name": "Distributed KV Store",
      "description": "Implemented Raft consensus in Go from scratch",
      "technologies": ["Go"],
      "metrics": ["Benchmarked throughput at 100k ops/sec"],
      "provenance": "resume_extracted"
    }
  ],
  "achievements": [],
  "metrics": [
    "Reduced API response latency by 40% across 50M daily requests",
    "Benchmarked throughput at 100k ops/sec"
  ],
  "employment_history": [
    {
      "company": "Synthetic Cloud Corp",
      "title": "Staff Backend Engineer",
      "start_date": "Jan 2022",
      "end_date": "Present",
      "is_current": true,
      "role_type": "full_time",
      "description": "Architected real-time event pipeline using Apache Kafka and Go",
      "highlights": ["Reduced API response latency by 40% across 50M daily requests"],
      "provenance": "resume_extracted"
    }
  ],
  "education": [
    {
      "institution": "University of Technology",
      "degree": "B.S.",
      "field_of_study": "Computer Science",
      "graduation_year": "2019",
      "provenance": "resume_extracted"
    }
  ],
  "summary": "Backend engineer specializing in distributed systems, Go, and cloud architecture.",
  "extraction_warnings": []
}
```

### Mapping to `PersonRecord`
Person 1 can map this directly into existing `PersonRecord` fields without database/schema changes:
1. `PersonRecord.skills`: `resume_data["skills"]`
2. `PersonRecord.employment_history`: `resume_data["employment_history"]`
3. `PersonRecord.education`: `resume_data["education"]`
4. `PersonRecord.resume_highlights`:
   ```python
   resume_highlights = (
       [{"type": "project", "name": p["name"], "technologies": p["technologies"], "metrics": p["metrics"]} for p in resume_data["projects"]]
       + [{"type": "metric", "content": m} for m in resume_data["metrics"]]
       + [{"type": "achievement", "content": a} for a in resume_data["achievements"]]
   )
   ```
5. `PersonRecord.source_metadata`:
   ```python
   {"source": "resume_extracted", "warnings": resume_data["extraction_warnings"]}
   ```

---

## 6. Hard-Filter Rules & Stable Reason Codes

Hard filters run first in `build_candidate_deck`. Any failed hard filter immediately sets `eligible = False`, assigns `rank = None`, and routes the candidate to `excluded_evaluations`.

### Filter Order & Evaluation
1. `must_have_skills`: Evaluated using deterministic case-insensitive normalization and alias mapping.
2. `mandatory_qualifications`: Checked against candidate education and achievements.
3. `min_experience_years` / `max_experience_years`: Numeric check. Fails closed with `experience_unknown_required` if minimum experience is required but candidate experience is unknown.
4. `required_fields`: Fails closed if candidate lacks the demanded field (`availability_unknown_required`, `salary_unknown_required`, `resume_missing_required`, `location_unknown_required`).
5. `dealbreakers`: Enforces mandatory location / work-mode constraints (`location_mismatch`, `work_mode_mismatch`).

### Missing Optional Data Policy
Missing optional fields (e.g., preferred skills, unstated candidate salary preferences) **remain unknown and never cause exclusion**.

---

## 7. Deterministic Fit Scoring Engine

Scoring evaluates eligible candidates across 5 weighted components:
$$\text{fit\_score} = 0.30 \cdot \text{skills} + 0.25 \cdot \text{experience} + 0.20 \cdot \text{role\_domain} + 0.15 \cdot \text{trajectory} + 0.10 \cdot \text{context}$$

- **Component Score Bounds**: Each component is bounded in $[0.0, 100.0]$.
- **Anti-Inflation Policy for Sparse Profiles**:
  - If a component has no documented evidence in the candidate profile, its score is $0.0$.
  - Missing component weights are **not redistributed**. This ensures sparse profiles are not artificially inflated.
- **Evidence Coverage Indicator**:
  - `evidence_coverage` ($0.0 \dots 1.0$) measures how many of the 5 dimensions have factual backing.
- **Explainability**: Every component appends human-readable reasons citing factual evidence.

---

## 8. Direct vs. Adjacent Classification & Threshold Calibration

Only candidates who pass all hard filters are classified.

### Engineering Default Thresholds (Subject to Team Calibration)
| Parameter | Default | Purpose |
|---|---|---|
| `DEFAULT_DIRECT_MIN_SCORE` | `70.0` | Minimum `fit_score` for Direct Fit. |
| `DEFAULT_ADJACENT_MIN_SCORE` | `50.0` | Minimum `fit_score` for Adjacent Fit. |
| `MIN_DIRECT_SKILLS_SCORE` | `60.0` | Minimum skill score for Direct Fit. |
| `MIN_DIRECT_ROLE_DOMAIN_SCORE` | `70.0` | Requires strong or exact title alignment for Direct Fit. |
| `MIN_ADJACENT_TRANSFERABLE_SKILLS` | `40.0` | Demonstrates transferable competence for Adjacent Fit. |
| `MIN_ADJACENT_ROLE_DOMAIN_SCORE` | `35.0` | Minimum functional domain relevance (excludes unrelated roles). |

- **Direct Fit**: Strong alignment on title, must-have skills, and domain.
- **Adjacent Fit**: Passes all hard filters, strong transferable capabilities, but misses preferred criteria or literal title alignment.
- **Unclassified (`None`)**: Candidates with insufficient score ($< 50.0$) or insufficient evidence receive `fit_type = None` and are **never** included in the displayed deck (routed to `excluded_evaluations` with `exclusion_reasons = ["insufficient_fit_or_evidence"]`).

---

## 9. Dynamic Deck Assembly & Adjacent Cap Rules (`build_candidate_deck`)

`build_candidate_deck` returns `(displayed_evaluations, excluded_evaluations)`.

1. **Target Deck Size**: At most 20 cards (`min(deck_size, 20)`).
2. **Adjacent-Fit Cap**:
   - The adjacent share is a **strict maximum of 20% of the actual displayed deck**, and at most 4 cards in a 20-card deck:
     $$\text{num\_adjacent} \le \min\left(4, \lfloor \text{len}(\text{displayed}) \times 0.20 \rfloor\right)$$
   - If total displayed is 20: at most 4 adjacent.
   - If total displayed is 15: at most 3 adjacent.
   - If total displayed is 10: at most 2 adjacent.
   - If total displayed is 5: at most 1 adjacent.
   - If 0 direct candidates exist: 0 adjacent cards displayed.
3. **No Forced Filler**: If fewer than 20 eligible, high-quality candidates exist, return only available strong candidates. Never add weak adjacent candidates as filler.
4. **Deterministic Ranking**:
   - Displayed cards are ordered by `(-fit_score, -evidence_coverage, person_id)`.
   - Assigned ranks: $1, 2, \dots, N$.
   - Excluded evaluations always have `rank = None`.
5. **No Candidate Overlap**: A candidate appears in exactly one output list (displayed OR excluded).

---

## 10. Match Explanation Generation & Fallback

- Every displayed card includes a grounded `match_explanation` and `reasons`.
- **Deterministic Template Fallback**: Built-in evidence-grounded template is used automatically if Claude is unconfigured, times out, or encounters a network error.
- **Explanation failure never breaks deck generation, scoring, or ranking.**

---

## 11. Known Boundaries & Non-Functional Guarantees

1. **Zero External Outreach**: No real candidates are contacted.
2. **Untrusted Data Directives**: All JD text and resume plain text are treated as untrusted data; prompt injection attempts are neutralized.
3. **Protected Characteristics Excluded**: No age, gender, race, religion, or disability information is evaluated or stored.
4. **No Direct Crustdata Dependency**: Person 2 does not call Crustdata APIs; Person 1 supplies normalized `PersonRecord` inputs.
