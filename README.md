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
    DEEPGRAM_API_KEY=your-deepgram-api-key

    OPENAI_API_KEY=your-openai-api-key

    LIVEKIT_URL=your-livekit-url
    LIVEKIT_API_KEY=your-livekit-api-key
    LIVEKIT_API_SECRET=your-livekit-api-secret

    AWS_ACCESS_KEY_ID=your-aws-access-key-id
    AWS_SECRET_ACCESS_KEY=your-secret-access-key
    AWS_REGION=your-aws-region

    PINECONE_API_KEY=your-pinecone-api-key
    PINECONE_ENV=your-pinecone-env
    PINECONE_INDEX_NAME=your-pinecone-index-name

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