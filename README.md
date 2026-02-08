# 🧭 LiveKit Voice Real Estate Agent

An AI-driven voice real estate agent backend that powers real-time voice conversations over LiveKit, with intelligent property search via Pinecone and natural language handling with OpenAI—supporting English and Japanese.

---

## 📚 Table of Contents

[About](#-about)  
[Features](#-features)  
[Tech Stack](#-tech-stack)  
[Installation](#️-installation)  
[Usage](#-usage)  
[Configuration](#-configuration)  
[Screenshots](#-screenshots)  
[API Documentation](#-api-documentation)  
[Acknowledgements](#-acknowledgements)

---

## 🧩 About

This project provides a voice-first interface for real estate discovery and lead capture. It solves the need for an always-available, multilingual AI agent that can understand buyer preferences, search properties semantically, and collect contact information—all over real-time voice using LiveKit.

Key goals: multi-language (EN/JA) voice interaction, vector-based property search, consent-based lead capture, and seamless integration with LiveKit rooms and RPC for frontend updates.

---

## ✨ Features

- **Multi-language voice** – English and Japanese with automatic detection and language-specific TTS/STT.
- **Real-time voice over LiveKit** – Bidirectional audio, room management, and participant attributes.
- **Semantic property search** – Vector search with Pinecone and OpenAI embeddings for natural-language queries.
- **Structured conversation flow** – Greeting → consent → requirements → search → details → contact capture → follow-up.
- **Contact & lead capture** – Form display and submission via RPC for interested users.
- **Function tools** – `search_real_estate`, `show_contact_form`, `submit_contact_info`, `get_language`, `initial_greeting`.

---

## 🧠 Tech Stack

| Category   | Technologies |
|-----------|---------------|
| **Languages** | Python 3.8+ |
| **Frameworks** | LiveKit Agents SDK |
| **AI / ML** | OpenAI (GPT-4o-mini, text-embedding-3-small), Deepgram (STT), Google Cloud TTS |
| **Database** | Pinecone (vector store) |
| **Tools** | python-dotenv, Silero VAD, BVC noise cancellation |

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dwilar-voice-agent-v1.git

# Navigate to the project directory
cd dwilar-voice-agent-v1

# Create and activate a virtual environment (recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Initialize the Pinecone index and upload property data:

```bash
python vectordb.py
```

---

## 🚀 Usage

```bash
# Run the main agent
python agent.py
```

Then connect your frontend or LiveKit client to your LiveKit room. The agent joins the room and handles voice conversations, property search, and contact collection.

👉 Use your LiveKit dashboard or client app to join a room and talk to the agent.

---

## 🧾 Configuration

Create a `.env` file in the project root with:

```env
# Deepgram (Speech-to-Text)
DEEPGRAM_API_KEY=your-deepgram-key

# OpenAI (LLM + embeddings)
OPENAI_API_KEY=your-openai-api-key

# LiveKit
LIVEKIT_URL=your-livekit-url
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENV=your-pinecone-env
PINECONE_INDEX_NAME=your-pinecone-index-name

# Google Cloud TTS
GOOGLE_APPLICATION_CREDENTIALS=./google-application-credentials.json
```

Place your Google Cloud service account JSON as `google-application-credentials.json` (or the path you set in `GOOGLE_APPLICATION_CREDENTIALS`).

---

## 🖼 Screenshots

Add demo images, GIFs, or UI preview screenshots of the voice agent or frontend here.

<!-- Example:
![Agent in action](./docs/screenshot.png)
-->

---

## 📜 API Documentation

The agent exposes **LiveKit RPC methods** for frontend integration:

| Method | Description |
|--------|-------------|
| `initData` | Send property search results to the frontend |
| `showContactForm` | Trigger display of the contact collection form |
| `submitContactInfo` | Submit collected contact details |
| `getContactInfo` | Retrieve stored contact information |

**Function tools** used by the assistant:

- `search_real_estate()` – Vector-based property search
- `show_contact_form()` – Display contact form
- `submit_contact_info()` – Process contact submission
- `get_language()` – Current language setting
- `initial_greeting()` – Introduction message

---

## 🌟 Acknowledgements

- **LiveKit** – Real-time audio and room infrastructure  
- **OpenAI** – GPT-4 and embeddings for conversation and search  
- **Pinecone** – Vector database for semantic property search  
- **Google Cloud TTS** – High-quality text-to-speech  
- **Deepgram** – Speech-to-text with language detection  
- **Dwilar Company** – Real estate platform and use case

---

*This project is part of the Dwilar Company real estate platform.*
