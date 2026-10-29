# Settings, read from environment variables with defaults for local development.

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rag:rag@localhost:5433/rag")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Changing the embedding model can change the vector size (768 here):
# update `vector(768)` in schema.sql and re-upload every document.
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# Which chat model writes the answers: "ollama" (local, free) or "claude" (paid API,
# needs ANTHROPIC_API_KEY). Embeddings always stay on Ollama.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
