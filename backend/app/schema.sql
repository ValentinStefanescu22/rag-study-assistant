-- Runs on every backend startup; IF NOT EXISTS makes that safe.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    filename    TEXT NOT NULL UNIQUE,
    page_count  INTEGER NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id          SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,        -- 1-based, as shown in a PDF viewer
    content     TEXT NOT NULL,
    embedding   vector(768) NOT NULL     -- nomic-embed-text outputs 768 numbers
);

-- Approximate nearest-neighbour index. `vector_cosine_ops` must match the `<=>`
-- (cosine distance) operator used in search queries, or Postgres won't use it.
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
