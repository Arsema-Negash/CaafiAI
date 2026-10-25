# CAAFI_AI — Clinical Guideline Retrieval MVP

CAAFI_AI is an early research prototype intended to make trusted health information easier to access. This repository currently implements a **source-linked clinical-guideline retrieval API** using the Ethiopian Primary Health Care Clinical Guidelines (2017).

> **Safety notice:** This is not a medical device, a diagnostic system, or a validated triage tool. It does not assess clinical urgency and must not be used as a substitute for a qualified health professional. The guideline is from 2017; confirm that it remains appropriate before any real-world use. For a possible emergency, seek urgent medical care.

## What currently works

- Extract text from a locally supplied guideline PDF.
- Chunk the text while retaining population, topic, page, and source metadata.
- Generate sentence-transformer embeddings and save them to a local JSON index.
- In-memory chunk and mtime-aware index caching for fast retrieval.
- Fast, local-cached SentenceTransformer loading with offline resilience.
- Retrieve semantically similar passages, with light topic/population ranking adjustments.
- Serve `GET /`, `GET /health`, `GET /ready`, `POST /chat`, and `POST /api/consultation` through FastAPI.
- Return retrieved passages and source/page metadata, with the response body quoting those passages only. Passages below the configured cosine-similarity floor are withheld (`evidence_status: "insufficient"`). The API deliberately does **not** invent a diagnosis or claim to assess urgency.
- Safe structured logging without logging patient query contents or sensitive clinical inputs.
- Run automated tests (`pytest`) for the API contract, retrieval ranking, chunk boundaries, text cleanup, and privacy logging.
- Evaluate retrieval quality against a draft labeled set plus robustness queries (`python -m app.ai.evaluate_retrieval`).

## Not implemented yet

- A generative LLM that rewrites answers (the API only quotes retrieved passages; it does not generate new clinical prose).
- Clinically validated emergency triage, diagnosis, or treatment recommendations.
- Amharic and other language generation, language identification, or local-slang normalization.
- SMS, telephone, speech-to-text, or text-to-speech integration.
- Production deployment, authentication, monitoring, and clinical evaluation.

These require additional engineering, external service configuration where applicable, and clinical review. Do not describe the current prototype as production-ready.

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

## Models actually used

There is **no generative language model** in this repository. Consultation answers are extractive quotes of retrieved guideline chunks.

| Role | Model | Provider / runtime | Network / keys |
|---|---|---|---|
| Query and document embeddings | `all-MiniLM-L6-v2` (384-dimensional) | `sentence-transformers` on local CPU/GPU via PyTorch | First load may download weights from Hugging Face if they are not already cached. Later loads use `local_files_only=True` when possible. **No API key.** |
| Answer generation | None | Extractive quoting in `app/core/ai_engine.py` | Offline |

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

The MVP supports English (`"language": "en"`). Messages exceeding 2,000 characters or non-English requests return HTTP 422. If the embedding index is missing, unreadable, built with a different embedding model, or the embedding model fails to load, HTTP 503 is returned with a generic service-unavailable message (internal exception text is not sent to the client). When no passage meets `MIN_SEMANTIC_SCORE`, HTTP 200 is still returned with `evidence_status: "insufficient"`, empty `sources`, and a limitation message that does not reassure the user.

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
2. Add a grounded LLM answer generator only after retrieval, citation, and evaluation quality are measured, and only with prompts that forbid unsupported clinical claims. This MVP must remain extractive until that work is approved.
3. Design and clinically evaluate an independent emergency escalation and triage layer.
4. Add multilingual support (Amharic, Afaan Oromoo, Somali) with fluent clinical translation and validation.
5. Add SMS and telephone channels with appropriate authentication, operational safeguards, and patient privacy controls.
