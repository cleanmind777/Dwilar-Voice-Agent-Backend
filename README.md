# Livekit-voice Backend

This is the backend for the Livekit-voice project. It provides an AI-powered real estate voice assistant using LiveKit, OpenAI, and Pinecone.

## Features
- Real estate search using natural language
- LiveKit agent integration for real-time voice calls
- OpenAI embeddings for semantic search
- Pinecone vector database for fast property retrieval

## Setup

1. **Clone the repository**
2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables**
   Create a `.env` file in the backend directory with the following variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENV=your_pinecone_env
   PINECONE_INDEX_NAME=your_pinecone_index_name
   # Add any other required keys (e.g., AWS for TTS)
   ```

## Running the Agent

```bash
python3 agent.py dev
```

- The agent will connect to your configured LiveKit cloud instance and listen for jobs.
- Make sure your environment variables are set and your Pinecone/OpenAI accounts are active.

## Notes
- This backend is designed to work with a Next.js frontend using LiveKit.
- For development, you may want to use test API keys and a test Pinecone index.
- See the code for more details on extending tools and agent logic. 