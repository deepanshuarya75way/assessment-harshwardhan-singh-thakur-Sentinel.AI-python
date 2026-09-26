# Dockerfile — deploys the FastAPI + LangChain backend to Hugging Face Spaces.
#
# HF Spaces (Docker SDK) expects the container to listen on port 7860.
# Build size is larger than a typical FastAPI app because of PyTorch +
# sentence-transformers (the local Hugging Face embedding model) — this is
# exactly why we're using HF Spaces instead of a memory-limited free tier
# elsewhere: Spaces gives 16GB RAM on the free CPU tier, which this needs.

FROM python:3.11-slim

WORKDIR /app

# System deps needed by some ML wheels (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Hugging Face Spaces always expects port 7860 for Docker SDK spaces
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
