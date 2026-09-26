"""
Embeddings — fastembed (ONNX Runtime), swapped from sentence-transformers.

# Why I switched hosting from Hugging Face Spaces to Render:
# HF Spaces paywalled the Docker SDK on the free cpu-basic tier in July 2026
# (Gradio and Streamlit got the same treatment — only Static Spaces stayed
# free, and Static can't run a Python backend at all). Render's free web
# service tier doesn't need a card, so that's where this is deployed now.
#
# Why I switched sentence-transformers to fastembed:
# Render's free tier only gives 512MB RAM. sentence-transformers pulls in
# full PyTorch under the hood, which alone can eat 300-400MB before the app
# even starts — the container built fine and passed the health check, but
# OOM-crashed the moment a real /query request tried to actually load the
# embedding model. fastembed runs the exact same model architecture through
# ONNX Runtime instead of PyTorch, which cut memory use enough to survive a
# real request on 512MB. No torch dependency at all now.
#
# Same model name works with both libraries (all-MiniLM-L6-v2 is in
# fastembed's supported model list), so retrieval quality/output is
# unchanged — this is purely a runtime swap, not a model swap.
"""

from functools import lru_cache

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> FastEmbedEmbeddings:
    """
    Cached singleton — the model is loaded into memory once and reused,
    same pattern as before. Now called eagerly at app startup (see
    main.py's startup_event) instead of lazily on the first request, so
    a memory problem shows up in the deploy logs immediately instead of
    silently killing a live user's query.
    """
    return FastEmbedEmbeddings(
        model_name=settings.HF_EMBEDDING_MODEL,
        # Keeps the ONNX model cached on disk between restarts instead of
        # re-downloading it every cold start — small speedup, doesn't cost
        # extra RAM since it's a disk cache, not a memory cache.
        cache_dir=settings.FASTEMBED_CACHE_DIR,
        # Render's free tier gives 0.1 vCPU — no point spinning up parallel
        # ONNX threads it doesn't have cores for. Leave unset (None) so
        # onnxruntime picks its own sane default for a single-core box.
        threads=None,
    )
