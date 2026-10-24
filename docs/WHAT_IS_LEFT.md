# What is left — verified, not guessed

This file lists work that was **not** completed in the sandbox, and why. Nothing below is marked done.

## Done in the repository (engineering only)

- Source-linked retrieval API (`GET /`, `/health`, `/ready`, `POST /chat`, `POST /api/consultation`).
- Central config (`.env.example`, `app/core/config.py`).
- Privacy logging (query length and language only).
- Extractive answers: the response quotes retrieved chunks and does not call a generative model.
- Draft retrieval evaluation report (metadata labels only).
- Unsigned clinician checklist: `evaluation/CLINICAL_REVIEW_CHECKLIST.md`.

## Cannot be finished from this environment

| Item | Why it is still open | What you do |
|------|----------------------|-------------|
| GitHub push | No GitHub credentials here | From your PC: `git push origin main` |
| Full pytest on Python 3.13 | This sandbox is not your Windows `.venv` | `py -3.13 -m venv .venv` then `python -m pytest -q` |
| Live retrieval evaluation with MiniLM | `sentence-transformers` / torch were not reinstalled here | `python -m app.ai.evaluate_retrieval --output reports\retrieval-evaluation.json` |
| Clinician sign-off | A model must not invent a clinician's approval | A qualified reviewer fills `evaluation/CLINICAL_REVIEW_CHECKLIST.md` |
| Generative LLM answers | Would invent clinical prose unless a reviewed model and prompt exist | Do not add until a clinician accepts the retrieval layer |
| Emergency triage rules | Must not be invented or self-certified | Design only with a clinician and a current guideline |
| Amharic / Afaan Oromoo / Somali | Needs reviewed translations, not machine guesses presented as clinical text | Separate language project after English retrieval is reviewed |
| SMS / telephone | Needs a telecom provider, auth, and privacy review | Out of scope for this MVP |
| Production deploy, auth, HIPAA/GDPR | No production host, no user store, no compliance assessment was performed | Do not deploy for patient care |

## Push commands (Windows CMD)

```cmd
cd C:\Users\hp\Desktop\Caafi\CaafiAI
git status
git log -3 --oneline
git push origin main
```

Unpack this zip over a copy of the project, or replace the folder, then push. Local commits in this archive are ahead of `origin/main`.
