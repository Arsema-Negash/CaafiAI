# CAAFI_AI — Clinical Guideline Retrieval MVP

CAAFI_AI is an early research prototype intended to make trusted health information easier to access. This repository currently implements a **source-linked clinical-guideline retrieval API** using the Ethiopian Primary Health Care Clinical Guidelines (2017).

> **Safety notice:** This is not a medical device, a diagnostic system, or a validated triage tool. It does not assess clinical urgency and must not be used as a substitute for a qualified health professional. The guideline is from 2017; confirm that it remains appropriate before any real-world use. For a possible emergency, seek urgent medical care.

## What currently works

- Extract text from a locally supplied guideline PDF.
- Chunk the text while retaining population, topic, page, and source metadata.
- Generate sentence-transformer embeddings and save them to a local JSON index.
- Retrieve semantically similar passages, with light topic/population ranking adjustments.
- Serve `GET /health`, `GET /ready`, `POST /chat`, and `POST /api/consultation` through FastAPI.
- Return retrieved passages and source/page metadata. The API deliberately does **not** invent a diagnosis or claim to assess urgency.
- Run automated tests for the API contract, retrieval ranking, chunk boundaries, and text cleanup.

## Not implemented yet

- LLM-generated answers grounded in the retrieved passages.
- Clinically validated emergency triage, diagnosis, or treatment recommendations.
- Amharic and other language generation, language identification, or local-slang normalization.
- SMS, telephone, speech-to-text, or text-to-speech integration.
- Production deployment, authentication, monitoring, and clinical evaluation.

These require additional engineering, external service configuration where applicable, and clinical review. Do not describe the current prototype as production-ready.

## Project layout

```text
CaafiAI/
├── app/
│   ├── ai/                 # Embeddings and retrieval
│   ├── api/                # FastAPI consultation routes
│   ├── core/               # Consultation orchestration
│   └── data/               # PDF ingestion and chunking
├── data/                   # Local-only guideline and generated index (git-ignored)
├── tests/                  # Automated unit/API tests
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Setup on Windows CMD

Run commands from the repository root (`CaafiAI`). Python 3.13 is the current development target; use a compatible Python version supported by the installed PyTorch/sentence-transformers packages.

```cmd
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Copy the authorized clinical guideline PDF into `data\raw\`. The PDF is intentionally excluded from Git; do not commit clinical source documents or generated indexes unless you have explicit permission and a reviewed data policy.

Build the local knowledge index:

```cmd
python -m app.data.ingestion
python -m app.data.build_embeddings
```

Run automated tests:

```cmd
python -m pytest -q
```

Run the API locally:

```cmd
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore the API. Stop the server with `Ctrl+C`.

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
python -m pytest -q
python -m uvicorn app.main:app --reload
```

The first embedding build downloads the `all-MiniLM-L6-v2` model if it is not already cached, so internet access is required for the first run unless the model is provided separately. Generated files under root `data/` are local artifacts and are not pushed to GitHub.

## API

### `GET /health`

Confirms the API process is responding. It does not guarantee the embedding model or index is ready.

### `GET /ready`

Reports whether `data/embeddings/clinical_chunks.json` exists.

### `POST /api/consultation` or `POST /chat`

Request:

```json
{
  "message": "What guideline information is available about fever in a child?",
  "language": "en"
}
```

The current MVP supports English only. Other language values are rejected rather than falsely claiming that translation occurred. The response contains a short explanation, `severity: "not_assessed"`, `urgent: null`, source references, retrieved excerpts, similarity scores, and a safety disclaimer. Similarity scores are retrieval signals, not probabilities or clinical confidence.

## Development checks and retrieval evaluation

- `python -m pytest -q` runs automated unit/API/evaluation-script tests without requiring model downloads.
- `python -m app.ai.test_retrieval` runs the existing, small retrieval regression checks against the locally built embedding index and model.
- `python -m app.ai.evaluate_retrieval` evaluates the draft query set in `evaluation/retrieval_cases.json` and reports topic-label, population-label, and combined label hit rates at top 3 and top 5, plus joint mean reciprocal rank.
- Save a full JSON report when useful: `python -m app.ai.evaluate_retrieval --output reports/retrieval-evaluation.json`.
- The evaluation cases are **draft metadata checks, not a clinically validated gold set**. A qualified clinical reviewer must verify each query and expected topic/population label against an authorized, current guideline before the scores are used for clinical claims. The reported hit rates measure metadata-label agreement only, not clinical relevance, answer correctness, or safety.
- Rebuild the index after changing ingestion or chunking logic: `python -m app.data.ingestion` followed by `python -m app.data.build_embeddings`.

## Data, privacy, and Git

- Never commit `.env` files, API keys, patient information, or private clinical data.
- Root `data/` is ignored by Git, so the PDF, extracted text, and generated embedding index stay local.
- Keep an encrypted backup of source documents if you are authorized to retain them.
- Use synthetic data for development and testing.

## Roadmap

1. Complete retrieval evaluation with a reviewed set of representative questions.
2. Add a configurable LLM adapter that answers only from retrieved evidence and returns citations; test it with a supplied provider/model configuration.
3. Design and clinically review a separate emergency escalation layer before making any triage claims.
4. Add supported-language workflows and evaluate them with fluent speakers and healthcare professionals.
5. Add SMS/voice providers only after credentials, consent, privacy, and operational requirements are defined.
6. Add deployment, security, observability, and end-to-end evaluation before any real-world pilot.
