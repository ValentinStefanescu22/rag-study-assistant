# Settings, read from environment variables with defaults for local development.

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rag:rag@localhost:5433/rag")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Changing the embedding model can change the vector size (768 here):
# update `vector(768)` in schema.sql and re-upload every document.
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
