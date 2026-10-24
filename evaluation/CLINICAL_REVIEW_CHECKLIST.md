# Clinical Review Checklist (Pending Human Review)

**Status:** Draft engineering checklist only. **No clinician has signed this off.**
Do not treat any retrieval evaluation metric as clinical validation.

This checklist is intended for a qualified clinician (or clinical governance process) reviewing CAAFI_AI against an authorized, current clinical guideline source.

## Scope of this prototype

- Source currently encoded: Ethiopian Primary Health Care Clinical Guidelines, 2017.
- Capability: semantic retrieval of guideline passages with topic/population metadata.
- Explicitly **not** implemented: diagnosis, prescribing, automated triage, urgency scoring, or treatment orders.

## Review items

For each evaluation case in `evaluation/retrieval_cases.json` and for a broader sample of real clinical questions:

1. **Source currency** — Confirm whether the 2017 guideline (or the specific section) remains appropriate, or identify the superseding document.
2. **Topic/population labels** — Verify that expected_topic and expected_population match the actual guideline structure.
3. **Retrieval relevance** — For top-k results, are the returned passages clinically on-topic and not misleading when read in isolation?
4. **Missing evidence** — When the system returns no relevant passage, is the limitation message clear and non-reassuring?
5. **Urgency language** — Does any returned text or API field incorrectly imply that urgency was assessed? (API should keep `severity: not_assessed`, `urgent: null`.)
6. **Dangerous omission risk** — Are there high-stakes queries (e.g., severe dehydration, seizures, breathing difficulty) where retrieval routinely misses critical danger-sign content?
7. **Population mismatch** — Child vs adult guidance: does ranking correctly prefer the intended population when the query is unambiguous?
8. **Source traceability** — Are page, topic, population, and source fields sufficient for a clinician to locate the original text?
9. **Language and literacy** — Is English-only output acceptable for the intended users? What Amharic or local-language gaps exist?
10. **Deployment boundary** — What additional controls (authentication, audit, human-in-the-loop, updated guideline) are required before any non-research use?

## Sign-off fields (to be completed by reviewer)

| Field | Value |
|-------|--------|
| Reviewer name / credentials | _pending_ |
| Date | _pending_ |
| Guideline version reviewed | _pending_ |
| Cases reviewed (IDs or count) | _pending_ |
| Overall recommendation | _pending_ (e.g., not ready / limited research use only / further revision required) |
| Critical findings | _pending_ |

## Engineering notes for reviewers

- Metrics in `reports/retrieval-evaluation.json` measure **metadata label agreement only**.
- They do **not** measure clinical correctness, completeness, or safety.
- The API never invents diagnoses; it returns retrieved passages or a clear limitation.
