---
title: Sentinel AI Backend
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Sentinel.AI Backend (LangChain Edition)

FastAPI + LangChain + Hugging Face reimplementation of the original Node.js
multi-agent RAG pipeline. See the main repo for full documentation:
https://github.com/HarshThakur47/Sentinel.AI-python

**Live API docs:** once this Space is running, visit `/docs` on this Space's
URL for interactive Swagger UI.

## Required Space secrets (set under Settings → Repository secrets)

| Secret | Required | Notes |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | From openrouter.ai/keys |
| `JWT_SECRET_KEY` | Yes | Any random string |
| `DEMO_USERNAME` | Yes | Matches frontend's `VITE_DEMO_USERNAME` |
| `DEMO_PASSWORD` | Yes | Matches frontend's `VITE_DEMO_PASSWORD` |
| `EXTRA_ALLOWED_ORIGINS` | Yes | Your deployed Vercel frontend URL(s), comma-separated |
