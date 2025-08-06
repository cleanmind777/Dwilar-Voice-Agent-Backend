# LiveKit Voice Real Estate Agent Backend

## Overview

This backend powers an AI-driven voice real estate agent using LiveKit for real-time communication, OpenAI for natural language processing, and Pinecone for vector-based property search. The agent can communicate in both English and Japanese and provides intelligent property recommendations based on user preferences.

## Features

- **Multi-language Support**: English and Japanese voice interaction
- **Real-time Voice Communication**: Using LiveKit infrastructure
- **Intelligent Property Search**: Vector-based semantic search using Pinecone
- **Contact Information Collection**: Automated lead capture with form integration
- **Natural Language Processing**: OpenAI GPT-4 for conversation management
- **Text-to-Speech**: Google Cloud TTS with language-specific voices

## Architecture

### Core Components

1. **Agent (`agent.py`)**: Main AI assistant implementation
2. **Vector Database (`vectordb.py`)**: Property data indexing and management
3. **Vector Search (`vectorsearch.py`)**: Property search functionality
4. **Prompt System (`prompt.py`)**: System prompts and conversation flow
5. **Alternative Agent (`agent1.py`)**: Simplified agent implementation

### Key Technologies

- **LiveKit**: Real-time audio communication and room management
- **OpenAI**: GPT-4 for conversation AI and embeddings for search
- **Pinecone**: Vector database for semantic property search
- **Google Cloud**: Text-to-speech services
- **Deepgram**: Speech-to-text transcription

## Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API key
- Pinecone API key
- LiveKit Cloud account
- Google Cloud account (for TTS)

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
PINECONE_INDEX_NAME=your_index_name
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-livekit-url
```

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize Pinecone index and upload property data:
```bash
python vectordb.py
```

3. Run the agent:
```bash
python agent.py
```

## Usage

### Agent Functionality

The AI agent follows this conversation flow:

1. **Initial Greeting**: Introduces itself as a Dwilar Company real estate agent
2. **Consent Collection**: Asks for user permission to collect information
3. **Property Requirements**: Collects location, price range, and bedroom count
4. **Property Search**: Performs vector search and presents top 3 matches
5. **Property Details**: Provides detailed information on selected properties
6. **Contact Collection**: Captures email and phone for interested users
7. **Follow-up**: Promises contact for property viewings

### Function Tools

The agent includes several function tools:

- `search_real_estate()`: Vector-based property search
- `show_contact_form()`: Display contact information form
- `submit_contact_info()`: Process collected contact details
- `get_language()`: Check current language setting
- `initial_greeting()`: Provide introduction message

### Language Support

The agent automatically detects and switches between:
- **English**: Using male Chirp-HD voice
- **Japanese**: Using female Chirp3-HD voice

Language switching is handled through participant attributes in the LiveKit room.

## Vector Search System

### Data Structure

Properties are stored in Pinecone with embeddings generated from:
- Property title
- Location/address
- Price information
- Number of bedrooms
- Property structure/type

### Search Algorithm

1. User input is converted to natural language query
2. Query is embedded using OpenAI's `text-embedding-3-small` model
3. Pinecone performs cosine similarity search
4. Top 3 most relevant properties are returned

### Sample Property Data

```json
{
  "title": "Modern 3BR House",
  "property_detail": {
    "PRICE": "$450,000",
    "BEDROOMS": "3",
    "PROPERTY TYPE": "House"
  },
  "description_detail": {
    "Address": "123 Main St, Tokyo, Japan"
  }
}
```

## API Integration

### LiveKit RPC Methods

The agent registers several RPC methods for frontend communication:

- `initData`: Send property search results to frontend
- `showContactForm`: Display contact collection form
- `submitContactInfo`: Process contact form submission
- `getContactInfo`: Retrieve stored contact information

### Real-time Communication

The agent uses LiveKit's real-time infrastructure for:
- Audio streaming (bidirectional)
- Room management
- Participant attribute synchronization
- RPC method calls for UI updates

## Configuration

### Audio Settings

- **STT**: Deepgram Nova-2 model with language detection
- **TTS**: Google Cloud TTS with voice variants per language
- **VAD**: Silero Voice Activity Detection (threshold: 0.7)
- **Noise Cancellation**: BVC (Background Voice Cancellation)

### LLM Configuration

- **Model**: GPT-4o-mini
- **Temperature**: 0.3 (balanced creativity/consistency)
- **Context**: Language-specific system prompts

## File Structure

```
backend/
├── agent.py              # Main AI agent implementation
├── agent1.py             # Alternative/simplified agent
├── vectordb.py           # Vector database management
├── vectorsearch.py       # Search functionality
├── prompt.py             # System prompts and instructions
├── requirements.txt      # Python dependencies
├── config/               # Configuration files
│   └── *.json           # Service account keys
└── KMS/                  # Key Management System
    └── logs/            # Application logs
```

## Dependencies

Key Python packages:

- `livekit-agents`: Real-time communication framework
- `openai`: AI language model and embeddings
- `pinecone-client`: Vector database client
- `google-cloud-texttospeech`: Text-to-speech services
- `python-dotenv`: Environment variable management

See `requirements.txt` for complete dependency list.

## Monitoring and Logging

The agent includes comprehensive logging for:
- User interactions and conversation flow
- Property search queries and results
- Contact information collection
- Language switching events
- RPC method calls and responses

## Troubleshooting

### Common Issues

1. **Connection Failures**: Check LiveKit credentials and network connectivity
2. **Search Not Working**: Verify Pinecone index exists and has data
3. **Language Not Switching**: Ensure participant attributes are set correctly
4. **TTS Issues**: Confirm Google Cloud credentials are properly configured

### Debugging

Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When modifying the agent:

1. Update system prompts in `prompt.py` for behavior changes
2. Modify vector search logic in `vectorsearch.py` for search improvements
3. Add new function tools to the `Assistant` class for additional features
4. Update environment variables documentation for new integrations

## License

This project is part of the Dwilar Company real estate platform. 