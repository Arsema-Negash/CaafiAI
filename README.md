# CAAFI_AI 🩺🤖

**CAAFI_AI** is an AI-powered health consultancy designed to make basic health guidance more accessible to people who may have limited access to nearby health facilities.

The system is being designed to allow users to communicate with the AI through **text and voice**, using their **native language and local expressions/slang**.

> 🚧 **Status:** Under active development

## 🎯 Goal

CAAFI_AI aims to provide accessible, multilingual health guidance through channels that are practical for users with limited access to healthcare services or digital infrastructure.

## ✨ Planned Features

* 💬 Health consultation through text
* 📞 Voice-based health consultation
* 🌍 Support for local/native languages
* 🗣️ Understanding of local expressions and slang
* 🧠 AI-powered health information and guidance
* 📚 Retrieval of information from trusted health resources
* 🚨 Symptom severity and emergency-risk detection
* 📱 SMS-based interaction
* 🔊 Speech-to-text and text-to-speech
* 🛡️ Safety-focused responses and referral to healthcare professionals when necessary

## 🏗️ Current Architecture

The project is being developed around a central health consultation API.

```text
User
 │
 ├── SMS
 │
 ├── Voice Call
 │
 └── Other Interfaces
        │
        ▼
   CAAFI_AI API
        │
        ▼
 Language Processing
        │
        ▼
 Safety & Triage
        │
        ▼
 Health Knowledge / RAG
        │
        ▼
 AI Reasoning
        │
        ▼
 Safe Health Response
```

## 🛠️ Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn

### AI / Machine Learning

* To be added during development

### Voice & Communication

* Speech-to-Text — planned
* Text-to-Speech — planned
* SMS integration — planned
* Voice-call integration — planned

### Knowledge & Data

* Trusted health resources
* Health documents
* Retrieval-Augmented Generation (RAG) — planned

## 📁 Project Structure

```text
CaafiAI/
│
├── app/
│   └── main.py
│
├── data/
│
├── tests/
│
├── .gitignore
├── README.md
└── requirements.txt
```

## 🚀 Current API

### Health Check

```http
GET /health
```

Returns:

```json
{
  "status": "CAAFI_AI is running"
}
```

### Chat

```http
POST /chat
```

Example request:

```json
{
  "message": "I have a headache",
  "language": "en"
}
```

> The current `/chat` endpoint is an early development version and does not yet provide real medical reasoning.

## ⚠️ Safety

CAAFI_AI is intended to provide **health information and guidance, not replace qualified healthcare professionals**.

The system will be designed to identify potentially urgent symptoms and encourage users to seek appropriate medical care when necessary.

Medical information used by the system should come from reliable and appropriately reviewed sources.

## 🗺️ Development Roadmap

* [x] Initial FastAPI backend
* [x] Health-check endpoint
* [x] Initial `/chat` endpoint
* [ ] Patient input validation
* [ ] Symptom and severity classification
* [ ] Safety and emergency triage
* [ ] Health knowledge base
* [ ] RAG pipeline
* [ ] AI response generation
* [ ] Multilingual support
* [ ] Local language/slang handling
* [ ] SMS integration
* [ ] Speech-to-text
* [ ] Text-to-speech
* [ ] Voice-call integration
* [ ] End-to-end testing
* [ ] Deployment

## 📌 Disclaimer

CAAFI_AI is an educational and research project under development. It is not a substitute for professional medical diagnosis, treatment, or emergency medical services.