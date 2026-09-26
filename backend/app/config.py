"""
Sentinel.AI (LangChain Edition) — Config

Mirrors backend/config/config.js from the original Node service so the two
implementations stay conceptually aligned. Reads from .env via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Server ──────────────────────────────────────────────
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    # Comma-separated list of extra origins allowed to call this API — used
    # to add the deployed Vercel URL(s) on top of the local dev origin above
    # without needing a code change per environment.
    EXTRA_ALLOWED_ORIGINS: str = ""

    # ── JWT Auth ────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    DEMO_USERNAME: str = "admin"
    DEMO_PASSWORD: str = "changeme123"

    # ── OpenRouter LLM API (same provider as Node backend) ──
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ── Agent Models ─────────────────────────────────────────
    FILTER_AGENT_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    GENERATOR_AGENT_MODEL: str = "anthropic/claude-3-haiku"
    EVALUATOR_AGENT_MODEL: str = "google/gemini-2.0-flash-001"

    # ── Embeddings ────────────────────────────────────────────
    # Model name is unchanged from the sentence-transformers days — same
    # model, fastembed just loads it through ONNX Runtime instead of
    # PyTorch (see app/services/embeddings.py for why I switched).
    HF_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Where fastembed caches the downloaded ONNX model on disk between
    # restarts. Render's free tier disk is ephemeral (wiped on redeploy),
    # so this doesn't survive a redeploy either way — it just avoids a
    # redundant re-download if the container merely restarts (e.g. after
    # a crash) without a fresh deploy.
    FASTEMBED_CACHE_DIR: str = "./fastembed_cache"

    # ── Vector Store ─────────────────────────────────────────
    VECTOR_STORE: str = "chroma"  # "chroma" | "pinecone"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "sentinel-docs"

    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "sentinel-docs"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        """FRONTEND_URL plus any comma-separated EXTRA_ALLOWED_ORIGINS entries."""
        origins = [self.FRONTEND_URL]
        if self.EXTRA_ALLOWED_ORIGINS:
            origins.extend(
                o.strip() for o in self.EXTRA_ALLOWED_ORIGINS.split(",") if o.strip()
            )
        return origins


settings = Settings()
