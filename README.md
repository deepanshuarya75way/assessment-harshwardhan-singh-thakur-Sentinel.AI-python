# Sentinel.AI — LangChain Edition

A from-scratch reimplementation of [Sentinel.AI](https://github.com/HarshThakur47/Sentinel-AI)
— a multi-agent RAG (Retrieval-Augmented Generation) system — rebuilt on
**FastAPI + LangChain + Hugging Face**, paired with the original React frontend
re-pointed at this new backend.

The original is a hand-rolled Node.js/Express implementation. This repo exists
to demonstrate the same architecture built with a different, framework-based
stack: same 4-step pipeline (retrieve → filter → generate → evaluate), same
OpenRouter-backed LLM agents, same UI — reimplemented with LangChain's
abstractions and a local Hugging Face embedding model instead of Gemini +
Pinecone.

**Live demo:** _add your Vercel URL here once deployed_
**API docs:** _add your Hugging Face Space `/docs` URL here once deployed_

---

## Repo structure

```
sentinel-ai-langchain/
├── backend/     ← FastAPI + LangChain + Hugging Face RAG API
└── frontend/    ← React + Vite UI (copy of the original, re-pointed at this backend)
```

Each folder is independently runnable and independently deployable — the
backend to Hugging Face Spaces, the frontend to Vercel.

---

## Architecture

**Pipeline:** a user query is embedded and searched against a Chroma vector
store → a **Filter Agent** (Llama 3.3 70B) removes irrelevant/unsafe results →
a **Generator Agent** (Claude 3 Haiku) writes a grounded answer, citing
sources or falling back to general knowledge if nothing relevant was found →
an **Evaluator Agent** (Gemini 2.0 Flash) independently fact-checks the
answer against the sources and assigns a 0–10 confidence score, optionally
rewriting the answer if it finds unsupported claims.

**Frontend:** React 19 + Vite SPA. A chat view drives the pipeline above and
renders the confidence score + cited sources per answer; an Ingestion view
lets you drag-and-drop PDFs, which get chunked and embedded into the vector
store live. Both views hit the backend through `src/lib/api.js`, which
transparently handles JWT login and attaches the token to every request.

### What changed vs. the original Node backend

| Original (Node/Express) | This service (Python) | Why |
|---|---|---|
| Hand-rolled Express routes/controllers | FastAPI routers | Auto-generated OpenAPI/Swagger docs at `/docs`, no hand-written docs |
| Manual `if` validation in controllers | Pydantic models (`app/schemas.py`) | Declarative — FastAPI rejects malformed requests before your code runs |
| Gemini embeddings + Pinecone (cloud, needs API keys) | Hugging Face `sentence-transformers` (local) + Chroma (local) | Runs with zero external API keys for retrieval — only the LLM calls need one |
| No auth layer | JWT via `OAuth2PasswordBearer` (`app/security.py`) | Demonstrates a real protected-endpoint pattern |
| Hand-rolled axios HTTP client for OpenRouter | LangChain's `ChatOpenAI` pointed at OpenRouter's OpenAI-compatible endpoint | No custom HTTP client needed |
| Manual prompt strings + `JSON.parse` per agent | LangChain `ChatPromptTemplate` + LCEL chains (`prompt \| llm \| parser`) per agent | Declarative chain composition |

Same 3 agents, same models, same orchestration logic and graceful-degradation
fallbacks — ported 1:1, just expressed through a different framework's
idioms.

---

## Running locally

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # then fill in OPENROUTER_API_KEY
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive Swagger UI.

### Frontend

```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`. Demo login (`admin` / `changeme123` by
default) happens silently on first request — no login screen needed.

---

## Deployment

- **Backend → Hugging Face Spaces** (Docker SDK). Needed because the backend
  loads a PyTorch-based embedding model locally — HF Spaces' free tier gives
  16GB RAM, well past what Render's free tier (512MB) can handle. See
  `backend/README_HF_SPACE.md` for the Space's required secrets.
- **Frontend → Vercel**, with root directory set to `frontend/`.

---

## Tech stack

**Backend:** FastAPI · LangChain (LCEL) · Hugging Face `sentence-transformers`
· Chroma · OpenRouter (Claude 3 Haiku, Llama 3.3 70B, Gemini 2.0 Flash) ·
Pydantic · JWT (`python-jose`)

**Frontend:** React 19 · Vite 8 · Lucide Icons · vanilla CSS
