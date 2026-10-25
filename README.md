# CAAFI_AI — Clinical Guideline Retrieval MVP

CAAFI_AI is an early research prototype intended to make trusted health information easier to access. It combines a source-linked clinical-guideline retrieval API with an experimental **browser-simulated voice consultation** using adapted Ethio-HealthBridge speech components and optional Gemini-grounded answer generation.

> **Safety notice:** This is not a medical device, a diagnostic system, or a validated triage tool. It does not assess clinical urgency and must not be used as a substitute for a qualified health professional. The guideline is from 2017; confirm that it remains appropriate before any real-world use. For a possible emergency, seek urgent medical care.

## What currently works

- Extract text from a locally supplied guideline PDF.
- Chunk the text while retaining population, topic, page, and source metadata.
- Generate sentence-transformer embeddings and save them to a local JSON index.
- In-memory chunk and mtime-aware index caching for fast retrieval.
- Fast, local-cached SentenceTransformer loading with offline resilience.
- Retrieve semantically similar passages, with light topic/population ranking adjustments.
- Serve the original guideline consultation API and the new `/api/call/text`, `/api/call/voice`, and `/api/call/audio/{filename}` endpoints.
- Retrieve source-linked passages from the existing local guideline index, skip obvious table-of-contents chunks, and optionally ask Gemini to explain only those passages. A basic guard rejects unsupported explicit page citations and dosage amounts; it is not a semantic proof. If generation is unavailable for English, use a clearly labelled extractive fallback.
- Adapt Ethio-HealthBridge's Gemini speech transcription, `edge-tts`/gTTS speech synthesis, and keyword red-flag detection for the simulated-call experience.
- Display a responsive phone-call UI with recording, mute, hang-up, timer, transcript, answer, source panel, audio replay, and typed fallback.
- Run automated tests (`pytest`) for the API contracts, retrieval ranking, grounded prompt construction, mocked audio turns, emergency short-circuit, and upload validation.

## Still limited / not clinically validated

- Real Amharic speech, translation, Gemini generation, and TTS require credentials/network access and must be verified on the target laptop.
- The red-flag detector is a keyword rule, not a clinically validated triage model; it may miss or over-trigger on symptoms.
- The bundled guideline is from 2017 and may not represent current practice.
- Production deployment, authentication, clinical review, and clinical evaluation are out of scope.

Do not describe the current prototype as production-ready or clinically validated.

## Project layout

```text
CaafiAI/
├── app/
│   ├── ai/                 # Embeddings, retrieval, and evaluation
│   ├── api/                # FastAPI consultation routes and schemas
│   ├── core/               # App configuration, settings, and consultation orchestration
│   └── data/               # PDF ingestion, chunking, and embedding generation
├── data/                   # Local-only guideline and generated index (git-ignored)
│   ├── raw/                # Source guideline PDF
│   ├── processed/          # Extracted plain text
│   └── embeddings/         # Generated chunks with 384-d MiniLM embeddings
├── evaluation/             # Draft retrieval evaluation queries and target metadata
├── reports/                # Evaluation output reports (retrieval-evaluation.json)
├── tests/                  # Automated unit, API, retrieval, and evaluation tests
├── pytest.ini              # Pytest configuration with pythonpath and test paths
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Development and testing dependencies
└── README.md               # Architecture and setup documentation
```

## Configuration & Environment Variables

Settings are centrally managed in `app/core/config.py` with environment variable overrides. Copy `.env.example` to `.env` for local overrides (never commit `.env`).

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Environment name (`development`, `production`, etc.) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `EMBEDDINGS_FILE` | `data/embeddings/clinical_chunks.json` | Path to generated chunks index |
| `RAW_DATA_DIR` | `data/raw` | Path containing source guideline PDFs |
| `PROCESSED_DATA_DIR` | `data/processed` | Path for extracted text files |
| `DEFAULT_TOP_K` | `3` | Default number of evidence chunks returned |
| `MAX_TOP_K` | `10` | Maximum allowable `top_k` results |
| `MAX_MESSAGE_LENGTH` | `2000` | Maximum character length for consultation queries |
| `MIN_SEMANTIC_SCORE` | `0.25` | Minimum cosine similarity required to return a passage (engineering abstention floor, not clinical validation) |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Local sentence-transformers model used for both document and query embeddings |
| `GUIDELINE_SOURCE_NAME` | `Ethiopian Primary Health Care Clinical Guidelines, 2017` | Source label stored on each chunk |
| `GEMINI_API_KEY` | unset | Enables cloud STT, Amharic query translation, and grounded answer generation for the call MVP |
| `GOOGLE_API_KEY` | unset | Compatibility alias for `GEMINI_API_KEY` |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` | Gemini model used by generation and translation |
| `ENABLE_GENERATIVE` | `true` | Set `false` to disable Gemini answer generation |
| `MAX_GENERATION_TOKENS` | `512` | Maximum configured generated output tokens |

## Models actually used

The project now has an optional generative layer after local guideline retrieval. It is not guaranteed to be factually correct and must be clinically reviewed.

| Role | Model / component | Provider / runtime | Network / keys |
|---|---|---|---|
| Query and document embeddings | `all-MiniLM-L6-v2` (384-dimensional) | `sentence-transformers` locally via PyTorch | Model weights must be installed/cached; no API key. |
| Grounded explanation | `gemini-2.5-flash-lite` by default | Google Gemini; receives retrieved guideline excerpts | `GEMINI_API_KEY`; without it English requests use source excerpts. |
| Speech-to-text | Gemini audio transcription prompt adapted from Ethio-HealthBridge | Google Gemini | `GEMINI_API_KEY`; network required. |
| Text-to-speech | `am-ET-MekdesNeural` / `en-US-JennyNeural`, then gTTS fallback | `edge-tts` / gTTS | Network required; no Gemini key for TTS. |
| Emergency red flags | Local phrase matching adapted from Ethio-HealthBridge | Local Python code, before retrieval/generation | No network/key; not clinically validated. |

The embedding model name is centralized in `app/core/config.py` (`EMBEDDING_MODEL_NAME`). `python -m app.data.build_embeddings` writes that name into a versioned index wrapper. A legacy JSON list of chunks is still loaded so an existing local index keeps working until you rebuild. If a wrapped index names a different model than the app config, retrieval raises an error instead of mixing vector spaces.

Rebuilding the index is required after changing `EMBEDDING_MODEL_NAME`. Do not treat MiniLM retrieval quality as clinical accuracy.

## Setup on Windows CMD

Run commands from the repository root (`CaafiAI`). Python 3.13 is the development target.

```cmd
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

If this virtual environment already existed, run the install command again so the test extra `httpx2` is present. That package is used only by Starlette's test client.

Copy the authorized clinical guideline PDF into `data\raw\`. The PDF is intentionally excluded from Git; do not commit clinical source documents or generated indexes unless you have explicit permission and a reviewed data policy.

Build the local knowledge index:

```cmd
python -m app.data.ingestion
python -m app.data.build_embeddings
```

Run automated tests:

```cmd
python -m pytest -v
```
*(or simply `pytest` from repository root)*

Run the API locally:

```cmd
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore the interactive OpenAPI documentation. Stop the server with `Ctrl+C`.

## Setup on Ubuntu

Install Python, `venv`, and pip first. Then, from the cloned repository:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Copy the authorized PDF to `data/raw/`, then run:

```bash
python -m app.data.ingestion
python -m app.data.build_embeddings
python -m pytest -v
python -m uvicorn app.main:app --reload
```

The first embedding build downloads the `all-MiniLM-L6-v2` model if it is not already cached. On subsequent runs, it loads from local cache without outbound network latency.

## API Endpoints

### `GET /`

Returns service metadata, documentation link, and prototype notices.

### `GET /health`

Confirms the API process is running and responding (status 200).

### `GET /ready`

Reports whether the clinical knowledge index exists on disk (`ready: true/false`, `clinical_index: "available"/"missing"`) and echoes the configured `embedding_model`.

### `POST /api/consultation` or `POST /chat`

Retrieve evidence passages grounded in the clinical guideline.

**Request:**

```json
{
  "message": "What danger signs should be assessed in a child with fever?",
  "language": "en"
}
```

**Response (HTTP 200):**

```json
{
  "response": "I retrieved 3 potentially relevant passage(s) from the clinical guideline. These are evidence excerpts, not a diagnosis or a validated triage decision. Review the source and page references below with a qualified health professional.",
  "language": "en",
  "severity": "not_assessed",
  "urgent": null,
  "evidence_status": "retrieved",
  "sources": [
    {
      "id": 361,
      "topic": "Fever",
      "population": "Child",
      "page": 135,
      "source": "Ethiopian Primary Health Care Clinical Guidelines, 2017",
      "content": "Give urgent attention to the child with a fever (temperature ≥ 38°C now or in the past 3 days) and any of:\n...",
      "similarity": 0.8123
    }
  ],
  "disclaimer": "CAAFI_AI is an early research prototype, not a medical professional..."
}
```

The legacy `/chat` and `/api/consultation` routes accept English only. The simulated-call `/api/call/text` and `/api/call/voice` routes accept English and Amharic; Amharic translation and generation require `GEMINI_API_KEY`. If the index is missing/unreadable or the embedding model fails to load, the call API returns HTTP 503. When no passage meets `MIN_SEMANTIC_SCORE`, the system reports `evidence_status: "insufficient"` and does not invent evidence.

## Retrieval Evaluation & Metrics

The repository includes an automated evaluation harness (`app/ai/evaluate_retrieval.py`) that evaluates queries against `evaluation/retrieval_cases.json`.

Run evaluation:

```cmd
python -m app.ai.evaluate_retrieval --output reports/retrieval-evaluation.json
```

### Evaluation Results (measured 2026-10-25, local MiniLM index)

Method: `python -m app.ai.evaluate_retrieval` against the local 454-chunk index, model `all-MiniLM-L6-v2`, `MIN_SEMANTIC_SCORE=0.25`, cutoffs k=3 and k=5. Label hits are metadata agreement only.

| Metric | Historical core baseline | Measured now |
|---|---|---|
| **Core joint topic/population hit rate @ 3** (15 original IDs) | 0.8000 (12/15) | **1.0000 (15/15)** |
| **All label-match joint hit rate @ 3** (18 queries, includes paraphrase/typo) | n/a | **0.9444 (17/18)** |
| **Missed label-match IDs** | `adult_cough`, `child_wheeze`, `child_emergency` | **`child_fever_typo` only** |
| **Out-of-scope withheld rate** (2 queries) | n/a | **1.0000 (2/2)** |

Robustness notes from this run:

- `child_fever_paraphrase` and `adult_cough_reworded` jointly hit at rank 1.
- `child_fever_typo` (`fevre in a chld`) returned **no** passages above the 0.25 floor (abstention, not a wrong-topic ranking). That is safer than a confident mismatch, but it is not spelling-tolerant retrieval.
- `out_of_scope_windows_password` and `out_of_scope_geography` were fully withheld.

Do not treat these numbers as clinical accuracy. Re-run locally after changing the index, model, or threshold.

### Root-Cause Fixes
- `adult_cough`: Mapped to `Breathing difficulty` on page 29 ("Cough or difficulty breathing") in the chunker, matching the guideline structure.
- `child_emergency`: Evaluates against `Emergency patient` on page 128 ("The emergency child"), disambiguated from `Injured child`.
- `child_wheeze`: The chunker added `Wheeze/tight chest` aliases, but the embeddings index had not been rebuilt since that change. Rebuilding the 454-chunk embeddings with batch encoding resolved the missing topic labels on pages 142–143.
- Population inference was improved to remain neutral (`None`) when both "adult" and "child" are present in a single query, preventing unfair penalties.


A structured **pending clinician review** checklist lives at `evaluation/CLINICAL_REVIEW_CHECKLIST.md`. It must remain unsigned until a qualified reviewer completes it.

### Clinical Limitation Notice
> **Important:** The evaluation cases are **draft engineering checks, not a clinically validated gold set**. The reported hit rates measure metadata-label agreement only, **not clinical relevance, answer correctness, or clinical safety**. A qualified clinical team must review all guideline sections, test cases, and expected behaviors before any patient-facing use.

## Data, Privacy, and Security

- **No Patient Data Logging:** The API logs request length and language code only (`caafi_ai.consultation: Processing consultation request: language=en, query_chars=44`). The query text and patient descriptions are never written to server logs.
- **Excluded Data:** The root `data/` directory is excluded from Git to prevent tracking local clinical source documents, extracted text, and embedding indexes.
- **No Hardcoded Secrets:** No API keys, passwords, or cloud credentials are stored in code. Configuration is loaded via environment variables with safe local defaults.
- **Offline Capable:** MiniLM embeddings load with `local_files_only=True` when cached, avoiding outbound network requests or timeouts during operation.
- **CI:** `.github/workflows/ci.yml` runs `python -m pytest` on Python 3.13. That workflow has been added in the repository; it is **not yet verified on GitHub Actions** until a push or pull request runs it.
- **Test client warning:** Starlette 1.7 still works with `httpx`, but TestClient prefers the `httpx2` package. `httpx2` is a **dev** dependency only so tests can silence that deprecation without changing production HTTP clients.

## Roadmap

1. Qualified clinician review of guideline currency (post-2017 updates), case evaluations, and expected label mappings.
2. Evaluate the optional grounded LLM generator against clinician-reviewed cases; keep the extractive fallback and reject unsupported or uncited claims.
3. Design and clinically evaluate an independent emergency escalation and triage layer.
4. Validate the current Amharic/English voice flow, then consider Afaan Oromoo and Somali only after reliable translation and clinical validation.
5. Add SMS and telephone channels with appropriate authentication, operational safeguards, and patient privacy controls.

---

## Simulated voice-call MVP (CAAFI_AI integration)

The browser interface at `/app` now simulates a voice consultation. It does not
place a real telephone call, contact an ambulance, or contact a clinician.

### Request flow

1. The browser requests microphone permission and records one question at a time
   with `MediaRecorder`; typed questions remain available as a fallback.
2. `/api/call/voice` uploads a short audio clip to the adapted Ethio-HealthBridge
   Gemini speech-transcription component. `/api/call/text` accepts typed turns.
3. A local keyword red-flag check runs before retrieval or answer generation. It
   returns a caution message only; it is not a validated triage model.
4. For Amharic questions, Gemini translates the question (including recent
   patient-turn context) into English for CAAFI_AI's existing English guideline
   index. The original language is requested for the generated answer. Obvious table-of-contents chunks are excluded from evidence retrieval.
5. CAAFI_AI retrieves passages from its existing `data/embeddings/clinical_chunks.json`
   index. Gemini is asked to explain only the retrieved excerpts. If generation
   is unavailable for English, the application falls back to clearly labelled
   source excerpts. Amharic consultation fails explicitly if Gemini is unavailable
   rather than presenting an English fallback as an Amharic answer.
6. The adapted Ethio-HealthBridge TTS component tries the Amharic `edge-tts`
   voice (`am-ET-MekdesNeural`) or an English neural voice, then attempts a gTTS
   fallback. Audio playback is optional; a failed TTS attempt does not replace or
   fabricate the text response.
7. The browser shows the transcript, response, source topic/page metadata, and
   plays the returned audio when the browser allows it. Follow-up context stays
   in browser memory and is sent with the next request; it is not persisted by
   the CAAFI_AI server.

### Ethio-HealthBridge reuse and attribution

Adapted components from <https://github.com/Illusionsp/ethio-healthbridge>:

- `backend/core/stt_engine.py`: Gemini audio upload and prompted transcription.
- `backend/core/tts_engine.py`: `edge-tts` neural voice with gTTS fallback.
- `backend/utils/emergency.py`: keyword red-flag pattern, extended with English
  phrases for this demo.
- `backend/core/rag_engine.py`: its Gemini-grounded RAG approach informed the
  generation integration, but its Chroma/LlamaIndex store is **not** imported
  as a second retrieval pipeline. CAAFI_AI keeps its own existing guideline
  index and passes retrieved evidence to Gemini.

The upstream MIT license and attribution notice are preserved in
`app/integrations/ethio_healthbridge/LICENSE` and `NOTICE.md`. Vision analysis,
Telegram doctor alerts, patient-ID memory, and outbreak tracking were not
integrated. The upstream RAG's empty-store fallback can return a basic LLM answer
without citations; that behavior was intentionally not reused.

### Setup on Windows

Open **Command Prompt** in the extracted project folder. If the project already
has a working `.venv`, activate it instead of creating another environment.

```bat
cd /d "C:\Users\hp\Desktop\Caafi\CaafiAI"
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
```

In `.env`, set `GEMINI_API_KEY` to a key from Google AI Studio. `GOOGLE_API_KEY`
can contain the same key as a compatibility alias. Keep the key in `.env`; never
paste it into frontend code or commit it. Gemini is required for cloud speech
transcription, Amharic-to-English query translation, and generative explanations.
The gTTS/edge-tts services also require network access. No key is required for
local retrieval alone, but the extractive fallback may be less conversational.

Run the test suite and server:

```bat
python -m pytest -v
python -m uvicorn app.main:app --reload
```

Open the interface at **<http://127.0.0.1:8000/app>**. API docs are at
<http://127.0.0.1:8000/docs>. Browser microphone access normally requires
`localhost` or HTTPS. If permission is blocked, use the typed-input fallback.

### Voice-call API contracts

- `POST /api/call/text` — JSON: `{"message":"...","language":"en|am","history":[{"role":"user|assistant","content":"..."}]}`.
- `POST /api/call/voice` — multipart fields: `audio` (browser audio clip),
  `language` (`am` or `en`), and `history_json` (JSON list of up to six turns).
- `GET /api/call/audio/{filename}` — serves only generated response MP3s.

The voice endpoint rejects unsupported media types and audio over 15 MB. Audio
uploads are written to a temporary file and deleted after processing. Generated
MP3s are stored under `data/audio_outputs/`; they are runtime artifacts and must
not be committed. A browser refresh clears the in-browser conversation history.

### Honest limitations before a live demonstration

- The bundled clinical guideline is the **2017** Ethiopian Primary Health Care
  Clinical Guidelines. This app does not establish that it is current or
  clinically validated.
- The Amharic STT, Gemini answer generation, Amharic translation, and speech
  synthesis require live network/provider access and must be tested with a real
  key on the target Windows laptop.
- The current environment used for this code pass did not have
  `sentence-transformers` installed, so real semantic retrieval could not run
  here. Install the project requirements and verify several distinct questions
  before presenting the MVP as a working end-to-end voice consultation.
- The emergency detector is keyword-based, may miss symptoms or flag negated
  phrases, and is not a validated clinical classifier. It does not call 912 or
  any other emergency service.
- Automated tests mock cloud transcription, generation, and TTS. They verify API
  contracts and fallback behavior, not the accuracy of real AI outputs.
