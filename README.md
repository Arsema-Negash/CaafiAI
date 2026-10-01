CAAFI_AI 🩺🤖

CAAFI_AI is an AI-powered health consultation system designed to make basic health guidance more accessible to people who may have limited access to nearby healthcare facilities.

The system is being developed to allow users to communicate with an AI health consultant through text messages and voice calls, using their native language and local expressions/slang.

CAAFI_AI combines AI reasoning, trusted health knowledge, Retrieval-Augmented Generation (RAG), multilingual processing, speech technologies, and safety-focused health triage into one system.

«🚧 Status: Under active development»

---

🎯 Vision

CAAFI_AI aims to provide accessible and safer health guidance for people who may have difficulty reaching healthcare facilities.

The goal is not to replace doctors or healthcare professionals, but to provide users with accessible health information, help them understand their symptoms, identify potentially urgent situations, and guide them toward appropriate care.

---

✨ Core Features

🧠 AI Health Consultation

CAAFI_AI will use an AI model to understand users' health concerns and provide responses grounded in trusted health information.

📚 Health Knowledge & RAG

The system will use trusted health resources, including relevant Ministry of Health materials, as a knowledge base.

Health Documents
       ↓
Document Processing
       ↓
Chunking & Embeddings
       ↓
Vector Database
       ↓
Relevant Knowledge Retrieval
       ↓
AI Model
       ↓
Grounded Response

🌍 Native Language & Local Slang

Users should be able to communicate using their native language and common local expressions or slang.

The system will work toward:

- Language identification
- Local expression understanding
- Medical terminology normalization
- Multilingual responses

📞 Voice Consultation

Users will eventually be able to call a dedicated number and communicate with CAAFI_AI through voice.

Phone Call
    ↓
Speech-to-Text
    ↓
CAAFI_AI
    ↓
AI Response
    ↓
Text-to-Speech
    ↓
Voice Response

💬 Text / SMS Consultation

Users will also be able to interact with CAAFI_AI through text-based communication, including SMS.

🚨 Safety & Triage

The system will include a safety layer designed to identify potentially urgent situations and recommend appropriate medical attention.

The AI should not confidently diagnose a patient from symptoms alone.

Instead, it should communicate uncertainty and provide appropriate guidance or referral when necessary.

---

🏗️ System Architecture

The planned architecture is:

                    USER
                      │
             ┌────────┴────────┐
             │                 │
          📞 Voice           💬 SMS/Text
             │                 │
             ▼                 ▼
        Speech-to-Text      Text Input
             │                 │
             └────────┬────────┘
                      ▼
              Language Processing
                      │
              Native Language
                 / Local Slang
                      │
                      ▼
              Symptom Understanding
                      │
                      ▼
                Safety / Triage
                      │
             ┌────────┴────────┐
             │                 │
          Urgent            Non-Urgent
             │                 │
             ▼                 ▼
       Urgent Guidance       RAG
                               │
                               ▼
                     Trusted Health Data
                               │
                               ▼
                         AI / LLM
                               │
                               ▼
                       Safety Validation
                               │
                               ▼
                       Final Response
                         /          \
                        ▼            ▼
                     Text          TTS
                                     │
                                     ▼
                                   Voice

---

🛠️ Technology Stack

Backend

- Python
- FastAPI
- Uvicorn

AI

- Large Language Model — planned
- Retrieval-Augmented Generation (RAG)
- Embeddings
- Vector database

Health Knowledge

- Ministry of Health resources
- Trusted health documents
- Structured health information

Language & Voice

- Speech-to-Text — planned
- Text-to-Speech — planned
- Multilingual processing — planned
- Local language/slang handling — planned

Communication

- SMS integration — planned
- Voice-call integration — planned

---

📁 Project Structure

The project will gradually evolve into a modular architecture:

CaafiAI/
│
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── services/
│   ├── data/
│   └── models/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── knowledge_base/
│
├── tests/
│
├── .gitignore
├── README.md
├── requirements.txt
└── run.py

The structure will be expanded as each component is implemented.

---

🚀 Current Development

The project currently contains the initial FastAPI backend.

Health Check

GET /health

Example response:

{
  "status": "CAAFI_AI is running"
}

Initial Consultation API

POST /chat

The current endpoint is an early API prototype. The actual AI health engine, knowledge retrieval, safety system, multilingual processing, SMS, and voice functionality are still under development.

---

🗺️ Development Roadmap

Phase 1 — Foundation

- [x] Initialize Python environment
- [x] Set up FastAPI
- [x] Create health-check endpoint
- [x] Create initial consultation endpoint
- [x] Set up GitHub structure

Phase 2 — Health Knowledge

- [ ] Identify trusted health sources
- [ ] Collect relevant health documents
- [ ] Process and clean documents
- [ ] Create knowledge-base pipeline
- [ ] Generate embeddings
- [ ] Set up vector database
- [ ] Implement RAG retrieval

Phase 3 — AI Health Engine

- [ ] Integrate AI model
- [ ] Build health consultation pipeline
- [ ] Ground responses in retrieved health information
- [ ] Handle uncertainty
- [ ] Add conversation context

Phase 4 — Safety & Triage

- [ ] Identify emergency warning signs
- [ ] Build safety layer
- [ ] Create escalation logic
- [ ] Test high-risk scenarios
- [ ] Prevent unsafe or overconfident medical responses

Phase 5 — Language

- [ ] Language identification
- [ ] Multilingual processing
- [ ] Local language support
- [ ] Local slang / expression handling
- [ ] Multilingual evaluation

Phase 6 — Communication

- [ ] SMS integration
- [ ] Speech-to-Text
- [ ] Text-to-Speech
- [ ] Voice-call integration
- [ ] Connect communication channels to the AI engine

Phase 7 — Testing & Evaluation

- [ ] Create test cases
- [ ] Evaluate RAG retrieval
- [ ] Evaluate language understanding
- [ ] Evaluate safety/triage
- [ ] Evaluate response quality
- [ ] Test voice and SMS flows
- [ ] Document limitations

Phase 8 — Deployment

- [ ] Configure production environment
- [ ] Secure API keys and secrets
- [ ] Deploy backend
- [ ] Configure communication services
- [ ] Final end-to-end testing

---

🔐 Safety & Privacy

CAAFI_AI is designed as a health-information and guidance system, not a replacement for qualified healthcare professionals.

The system should:

- Avoid presenting uncertain information as a diagnosis
- Identify potentially urgent symptoms
- Encourage professional medical care when appropriate
- Use trusted health sources for its knowledge base
- Protect sensitive user information
- Avoid storing real patient information in the public GitHub repository

Testing should use synthetic or appropriately anonymized data.

---

⚠️ Disclaimer

CAAFI_AI is an educational and research project under development.

It is not a substitute for professional medical diagnosis, treatment, or emergency medical services.

Users experiencing a medical emergency should seek appropriate emergency medical care immediately.

---

📌 Project Goal

«Making accessible, multilingual AI health guidance available through the communication methods people already use.»
