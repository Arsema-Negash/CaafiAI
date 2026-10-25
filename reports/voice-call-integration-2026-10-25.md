# CAAFI_AI voice-call integration report — 2026-10-25

## Scope

- Added a browser-simulated phone-call experience to the existing FastAPI app.
- Adapted Ethio-HealthBridge's Gemini speech transcription, `edge-tts`/gTTS
  synthesis, and keyword emergency rule; preserved the upstream MIT license and
  attribution notice.
- Activated CAAFI_AI's existing Gemini-grounded generation module after
  retrieval; retained the current local guideline index rather than introducing
  a second Chroma/LlamaIndex retrieval store.
- Added local red-flag short-circuiting, typed and audio API contracts, limited
  recent-turn context, upload limits, temporary upload cleanup, and source display.
- Carried forward the generic demographic/system-background ranking penalty and
  excluded obvious table-of-contents chunks from clinical evidence results.
- Added basic checks that reject explicit page citations and medication dose
  quantities not present in retrieved evidence; these checks are not a semantic
  proof of answer correctness.

## Test results

- Baseline on the uploaded `CaafiAI now.zip`: **57 passed in 0.59 seconds**.
- After changes: **77 passed in 0.42 seconds** (latest full suite run).
- Browser JavaScript syntax check: `node --check` completed without syntax errors.
- The `/app` page and call endpoints are exercised with FastAPI `TestClient`.
- Cloud STT, Gemini generation/translation, and TTS are mocked in tests; these
  tests do not verify provider output accuracy.

## Runtime verification limits

- A direct attempt to run real semantic retrieval for three separate queries
  failed before embedding/search because `sentence-transformers` is missing in
  this execution environment. The ZIP contains 454 precomputed chunks and the
  2017 guideline PDF/text, but this pass does not claim those chunks rank
  correctly for live symptom queries.
- No Gemini API key was available, so live audio transcription, Amharic query
  translation, grounded generation, and real spoken audio were not tested.
- Browser interaction was checked through API/static-page tests and JavaScript
  syntax checking; a real browser microphone/audio session was not run here.
- The uploaded ZIP contains no `.git` directory. Therefore, local branch status,
  pre-existing uncommitted Git changes, and an actual `git diff` could not be
  inspected. No commits were created, and only the extracted working copy was
  edited.

## Safety and product limitations

- The 2017 guideline may be outdated; no clinician review or clinical validation
  was performed.
- The red-flag layer is a conservative keyword matcher, not validated triage.
  It does not contact emergency services.
- Generative responses are instructed to use only retrieved excerpts, but a
  prompt cannot mathematically guarantee zero hallucinations. Real outputs and
  citations need manual clinical review before any live demonstration.
