# Sentinel.AI — LangChain Edition

A from-scratch reimplementation of [Sentinel.AI](https://github.com/HarshThakur47/Sentinel-AI)
— a multi-agent RAG (Retrieval-Augmented Generation) system — rebuilt on
**FastAPI + LangChain**, paired with the original React frontend re-pointed at
this new backend.

The original is a hand-rolled Node.js/Express implementation. This repo exists
to demonstrate the same architecture built with a different, framework-based
stack: same 4-step pipeline (retrieve → filter → generate → evaluate), same
OpenRouter-backed LLM agents, same UI — reimplemented with LangChain's
abstractions in place of hand-rolled prompt strings and HTTP clients.

**Live demo:** https://sentinel-ai-python.vercel.app
**API docs (Swagger):** https://sentinel-ai-python.onrender.com/docs
**Backend health check:** https://sentinel-ai-python.onrender.com/api/v1/health

> Both are on free hosting tiers. The backend spins down after ~15 minutes of
> inactivity, so the **first** request after a while can take 30–90 seconds to
> wake it back up — this is expected, not a bug. Subsequent requests are fast.

---

## Repo structure

```
sentinel-ai-langchain/
├── backend/     ← FastAPI + LangChain RAG API
└── frontend/    ← React + Vite UI (copy of the original, re-pointed at this backend)
```

Each folder is independently runnable and independently deployable — the
backend to Render, the frontend to Vercel.

---

## Architecture

**Pipeline:** a user query is embedded and searched against a Chroma vector
store → a **Filter Agent** (Llama 3.3 70B) removes irrelevant/unsafe results →
a **Generator Agent** (NVIDIA Nemotron 3 Super) writes a grounded answer,
citing sources or falling back to general knowledge if nothing relevant was
found → an **Evaluator Agent** (NVIDIA Nemotron 3 Super) independently
fact-checks the answer against the sources and assigns a 0–10 confidence
score, optionally rewriting the answer if it finds unsupported claims.

All three agents currently run on **free-tier OpenRouter models** (see
[Tech stack](#tech-stack)) so the whole pipeline runs at zero API cost.

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
| Gemini embeddings + Pinecone (cloud, needs API keys) | `fastembed` (ONNX Runtime, local) + Chroma (local) | Zero external API keys needed for retrieval — only the LLM calls need one. Also 5–10x lighter than a PyTorch-based embedding model, which matters on a 512MB free hosting tier |
| No auth layer | JWT via `OAuth2PasswordBearer` (`app/security.py`) | Demonstrates a real protected-endpoint pattern |
| Hand-rolled axios HTTP client for OpenRouter | LangChain's `ChatOpenAI` pointed at OpenRouter's OpenAI-compatible endpoint | No custom HTTP client needed |
| Manual prompt strings + `JSON.parse` per agent | LangChain `ChatPromptTemplate` + LCEL chains (`prompt \| llm \| parser`) per agent | Declarative chain composition |
| — | `/api/v1/documents/upload` (PDF → chunk → embed) | Added so the Ingestion tab has a real backend to call |

Same 3 agents, same orchestration logic and graceful-degradation fallbacks —
ported 1:1, just expressed through a different framework's idioms. Model
choices changed over the course of deployment (see [Deployment notes](#deployment-notes)
below) — the pipeline design didn't.

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

## Deployment notes

This went through two real pivots worth being upfront about, since they show
up in the git history and are a fair thing to be asked about:

**Backend hosting — Hugging Face Spaces → Render.** Originally targeted HF
Spaces for its generous free RAM. Docker-SDK Spaces on the free `cpu-basic`
tier were paywalled by Hugging Face in July 2026 (confirmed via their own
forums, not specific to this account). Moved to Render's free web service
tier instead — no card required, same `Dockerfile` works unchanged since it
already reads `$PORT` dynamically.

**Embeddings — `sentence-transformers` (PyTorch) → `fastembed` (ONNX
Runtime).** Render's free tier gives 512MB RAM. The container *built* and
passed its health check fine with the PyTorch-based embedding model, but
OOM-crashed the moment a real query tried to load it under actual request
load. Swapped to `fastembed`, which runs the identical `all-MiniLM-L6-v2`
model through ONNX Runtime instead of PyTorch — same output, 5–10x less
memory, no crash.

**LLM models — pinned versions → free-tier variants, twice.** Two of the
three original model picks (`anthropic/claude-3-haiku`, then separately
`google/gemini-2.0-flash-001`) were deprecated by OpenRouter mid-project.
Rather than re-pin to another paid model that could deprecate again, switched
all three agents to free-tier models (Llama 3.3 70B, NVIDIA Nemotron 3
Super), so the whole pipeline runs at zero ongoing cost. Trade-off: free-tier
models occasionally return a `503 provider_overloaded` under shared public
demand — rare, and the pipeline's existing error handling surfaces it
cleanly rather than crashing.

- **Backend → Render** (Docker runtime), root directory `backend/`.
- **Frontend → Vercel**, root directory `frontend/`.

---

## Known limitations (current, honest)

- **Cold start:** free Render instances sleep after ~15 min idle; first
  request after that can take 30–90s.
- **Free-model overload:** shared free-tier LLM capacity can occasionally
  return a transient `503`. Retrying the same request usually succeeds.
- **No persistent vector store:** Chroma's data lives in the container's
  ephemeral disk, so anything ingested via the Ingestion tab is wiped on
  every redeploy. Fine for a demo; a real deployment would use a persistent
  volume or a hosted vector DB.

---

## Tech stack

**Backend:** FastAPI · LangChain (LCEL) · `fastembed` (ONNX Runtime,
Hugging Face–sourced `all-MiniLM-L6-v2` model) · Chroma · OpenRouter
(Llama 3.3 70B, NVIDIA Nemotron 3 Super — free tier) · Pydantic ·
JWT (`python-jose`) · deployed on Render

**Frontend:** React 19 · Vite 8 · Lucide Icons · vanilla CSS · deployed on Vercel
