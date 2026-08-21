# AI-Powered Support Chatbot API

A production-style backend service for AI-powered conversations — built with FastAPI, PostgreSQL, and Groq's LLM API. Supports persistent multi-turn conversations, real-time streaming responses, per-user rate limiting, and a lightweight web chat UI.

**Live demo:** https://your-render-url.onrender.com/chat
**API docs (Swagger):** https://your-render-url.onrender.com/docs

---

## What this project demonstrates

This isn't a wrapper around an LLM call — the chatbot itself is one feature sitting on top of a properly engineered backend:

- Persistent conversation history stored relationally (not just stateless one-off calls)
- Real-time token-by-token streaming via Server-Sent Events (SSE)
- Per-user API key authentication
- Rate limiting to protect against abuse and quota exhaustion
- Paginated conversation retrieval
- Automated tests with the LLM call mocked (no network calls, no quota burned)
- Schema migrations managed with Alembic
- Deployed and live on Render, backed by a hosted PostgreSQL instance (Neon)

## Tech stack

| Layer | Tech |
|---|---|
| API framework | FastAPI (async) |
| Database | PostgreSQL (hosted on Neon) |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| LLM provider | Groq (`openai/gpt-oss-120b`) |
| Streaming | Server-Sent Events (SSE) |
| Rate limiting | slowapi |
| Testing | pytest, pytest-mock, SQLite (test DB) |
| Deployment | Render |
| Frontend | Vanilla HTML/CSS/JS (no framework, no build step) |

## Architecture

```
User (1) ──< Conversation (many) ──< Message (many)
```

- A `User` is identified by an API key sent in the `X-API-Key` header.
- Each `User` can have many `Conversations`.
- Each `Conversation` contains many `Messages`, each tagged with a `role` (`user` or `assistant`).
- On every new message, the last N messages (default 10) from the conversation are sent to the LLM as context — this keeps requests within Groq's per-minute token limit regardless of how long a conversation runs, while the full history remains stored in the database.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/conversations` | Start a new conversation |
| `GET` | `/conversations` | List the current user's conversations (paginated) |
| `GET` | `/conversations/{id}` | Get a conversation with full message history |
| `POST` | `/conversations/{id}/messages` | Send a message, get a full (non-streamed) AI reply |
| `POST` | `/conversations/{id}/messages/stream` | Send a message, get the AI reply streamed via SSE |
| `GET` | `/chat` | Serves the web chat UI |

All endpoints except `/` and `/chat` require an `X-API-Key` header.

## Key engineering decisions

- **SSE over WebSockets for streaming** — the data flow is one-directional (server → client token stream), so SSE is simpler to implement and sufficient; WebSockets would add unneeded complexity for this use case.
- **Conversation history truncation** — sending a full, unbounded conversation history to the LLM on every request eventually exceeds Groq's tokens-per-minute limit. The last N messages are sent as context instead, keeping token usage predictable.
- **Mocked LLM calls in tests** — tests patch the LLM call at the point of use (`app.main.get_ai_reply`) rather than at its definition, so the test suite runs fast, free, and deterministically without hitting a real API.
- **Rate limiting on LLM-calling endpoints** — protects the (free-tier) LLM quota from being exhausted by a single user or accidental request loop.

## Running locally

```bash
# Clone and enter the project
git clone https://github.com/YUVARAJC14/ai-chatbot-api.git
cd ai-chatbot-api

# Set up virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create a .env file with:
#   DATABASE_URL=postgresql+psycopg://user:password@host/dbname
#   GROQ_API_KEY=your_groq_api_key

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for the API, or `http://127.0.0.1:8000/chat` for the web UI.

## Running tests

```bash
pytest -v
```

Tests use an isolated SQLite database and mock all LLM calls — no real API requests are made.

## Possible future improvements

- Retrieval-augmented generation (RAG) using `pgvector` to let the bot answer from a custom knowledge base
- Summarizing older conversation turns instead of truncating them, to preserve more context within token limits
- User registration endpoint (currently users are seeded manually)

---

Built by [Yuvaraj C](https://github.com/YUVARAJC14)