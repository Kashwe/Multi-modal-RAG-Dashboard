# Multi-Modal RAG Dashboard

A free, end-to-end Retrieval-Augmented Generation demo built with **FastAPI**,
**LangChain**, **FAISS**, **sentence-transformers**, and **Groq** — with a
**Streamlit** front-end for uploads, chat, and live analytics.

Everything runs locally on free tiers (the only API key you need is a free
Groq key).

---

## Features (mapped to user stories)

| # | User story | Where it lives |
|---|---|---|
| 1 | Concurrent session handling (Redis + in-memory fallback) | [app/services/session_store.py](app/services/session_store.py) |
| 2 | Document parsing & chunking (PDF / DOCX / TXT / MD) | [app/services/document_parser.py](app/services/document_parser.py) |
| 3 | Embedding generation (local sentence-transformers) | [app/services/embeddings.py](app/services/embeddings.py) |
| 4 | FAISS vector indexing (per-session, persisted) | [app/services/vector_store.py](app/services/vector_store.py) |
| 5 | LangChain QA pipeline (Groq LLM) | [app/services/qa_chain.py](app/services/qa_chain.py) |
| 6 | Latency analytics | [app/services/analytics.py](app/services/analytics.py) + `/api/v1/analytics/latency` |
| 7 | Retrieval score analytics | same service + `/api/v1/analytics/retrieval` |
| 8 | Token usage monitoring | same service + `/api/v1/analytics/tokens` |

---

## Project layout

```
Multi-modal-RAG-Dashboard/
├── app/                          # FastAPI backend
│   ├── api/v1/
│   │   ├── api.py                # Aggregates all v1 routes
│   │   └── endpoints/
│   │       ├── sessions.py       # Story 1
│   │       ├── documents.py      # Stories 2-4
│   │       ├── query.py          # Story 5
│   │       └── analytics.py      # Stories 6-8
│   ├── core/
│   │   ├── config.py             # Pydantic settings, loads .env
│   │   └── logging.py
│   ├── schemas/                  # Pydantic request/response models
│   ├── services/                 # Core business logic
│   └── main.py                   # FastAPI app entry point
├── ui/                           # Streamlit front-end
│   ├── app.py
│   └── requirements.txt
├── data/                         # Runtime artifacts (gitignored)
│   ├── uploads/                  # User-uploaded files
│   └── faiss/                    # Persisted FAISS indexes
├── requirements.txt              # Backend deps
├── .env.example                  # Copy to .env, fill in GROQ_API_KEY
└── README.md
```

---

## Prerequisites

- **Python 3.12** (3.10+ should work, 3.12 verified)
- A free **Groq API key** — get one at https://console.groq.com/keys (no card)
- **Redis** is *optional* — the app falls back to an in-memory session store
  if Redis isn't reachable

---

## Setup

```powershell

# 1. Create and activate a virtual environment
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Install UI dependencies
pip install -r ui\requirements.txt

# 4. Configure environment
Copy-Item .env.example .env
notepad .env   # paste your GROQ_API_KEY
```

> On macOS / Linux replace the activation line with `source venv/bin/activate`
> and `cp .env.example .env`.

### Minimum `.env`

```dotenv
GROQ_API_KEY=gsk_your_real_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

All other settings have sensible defaults (see `.env.example`).

---

## Running the app

You need **two terminals** — one for the backend, one for the UI.

### Terminal 1 — backend (FastAPI)

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

- API root: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

If Redis isn't running you'll see a one-line warning — that's expected, the
in-memory fallback takes over.

### Terminal 2 — UI (Streamlit)

```powershell
.\venv\Scripts\Activate.ps1
streamlit run ui\app.py
```

UI opens at http://localhost:8501.

> The first time you upload a document, the ~80 MB sentence-transformers
> model downloads. This happens once and is cached locally.

---

## Using the demo

1. Open the Streamlit UI.
2. Click **Create session** in the sidebar.
3. **Upload tab** — drop a PDF / DOCX / TXT / MD file and click **Index files**.
4. **Chat tab** — ask a question about the document. The response shows the
   answer, latency breakdown (retrieval vs LLM), token counts, and source chunks.
5. **Analytics tab** — see live charts:
   - Latency line chart (recent queries)
   - Retrieval-score histogram (0.0–1.0 buckets)
   - Token-usage bar chart (prompt vs completion)
   - Per-session metrics

---

## API reference

All endpoints are under `/api/v1`. Full interactive docs at `/docs`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/sessions` | Create a session |
| `GET`  | `/sessions` | List sessions |
| `GET`  | `/sessions/{id}` | Session info (tokens, message count) |
| `DELETE` | `/sessions/{id}` | Delete a session |
| `POST` | `/documents/{session_id}` | Upload a file (multipart) |
| `GET`  | `/documents/{session_id}` | List documents in a session |
| `POST` | `/query/{session_id}` | Ask a question — returns answer + sources + metrics |
| `GET`  | `/analytics/latency` | Latency stats (avg, p50, p95, max, samples) |
| `GET`  | `/analytics/retrieval` | Retrieval scores (avg/min/max + histogram) |
| `GET`  | `/analytics/tokens` | Token usage (prompt / completion / total + per-query) |
| `GET`  | `/analytics/summary` | All three analytics in one call |
| `GET`  | `/analytics/sessions/{id}` | Per-session analytics |

---

## Optional — running Redis

For real concurrent-session isolation across worker processes, run Redis:

```powershell
# Easiest: Docker
docker run -d --name rag-redis -p 6379:6379 redis:7-alpine
```

The app auto-detects it via `REDIS_URL` in `.env`. No code change needed.

---

## Tech stack

- **Backend**: FastAPI, Pydantic v2, Uvicorn
- **Session store**: Redis (with thread-safe in-memory fallback)
- **Parsing**: `pypdf`, `python-docx`, plain text
- **Chunking**: LangChain `RecursiveCharacterTextSplitter`
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (local, free, 384-dim)
- **Vector store**: FAISS (CPU, persisted to disk per session)
- **LLM**: Groq (`llama-3.1-8b-instant` by default) via `langchain-groq`
- **Token counting**: `tiktoken` (falls back to Groq's `usage_metadata` when available)
- **UI**: Streamlit + pandas

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'langchain.text_splitter'`**
Run `pip install -r requirements.txt` again — newer langchain moved the
splitter into `langchain-text-splitters`.

**Redis warning at startup**
Expected if Redis isn't running. The in-memory store takes over.

**`groq_configured: false` on `/health`**
You haven't set `GROQ_API_KEY` in `.env`, or `.env` isn't being loaded. Make
sure `.env` is in the project root and you've restarted the server.

**First upload is slow**
The sentence-transformers model (~80 MB) downloads on the first call. Subsequent
uploads are fast.

**Port 8000 / 8501 already in use**
Pass an alternate port: `uvicorn app.main:app --reload --port 8010` or
`streamlit run ui\app.py --server.port 8520`. Update `RAG_API_BASE` env var
for the UI if you change the backend port.

---

## License

Demo project — no license specified. Add one before publishing.
