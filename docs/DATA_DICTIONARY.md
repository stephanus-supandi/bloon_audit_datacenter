# Data dictionary

## Finding

- `finding_id`: unique finding identifier.
- `project_id`: stable project/facility identifier; scope should be documented.
- `domain`: `civil`, `environmental`, `electrical`, `mechanical`, `it`, or `regulatory`.
- `category`, `requirement`, `observation`: concise finding metadata.
- `evidence_ids`: list of registered evidence IDs.
- `source_url`, `source_document`, `source_date`: primary reference metadata; do not guess source dates.
- `observation_date`: date the analyst recorded the observation.
- `verification_status`: `verified`, `partially_verified`, `unverified`, `not_applicable`, or `conflicting_evidence`.
- `severity`: `critical`, `high`, `medium`, `low`, or `undetermined`.
- `confidence`: numeric value in [0, 1], excluding booleans, NaN, and infinity.
- `limitations`, `reviewer_notes`: qualifications and audit trail.

## Evidence

Required fields: `evidence_id`, `title`, `issuing_org`, `url`, `access_date`, `is_verifiable`, `establishes`, and `unknowns`. `is_verifiable` describes whether the source itself is inspectable; it does not mean every claim is independently verified.
