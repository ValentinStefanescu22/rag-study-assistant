# All database access lives here, as plain SQL.

from pathlib import Path

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.config import DATABASE_URL

SCHEMA = Path(__file__).with_name("schema.sql").read_text()


def init_schema() -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(SCHEMA)


def connect() -> psycopg.Connection:
    # ponytail: new connection per call, switch to psycopg_pool if requests pile up
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    register_vector(conn)  # teaches psycopg how to send/receive the `vector` type
    return conn


# Store a document and its (page_number, text, embedding) chunks. Re-uploading a filename replaces it.
def save_document(filename: str, pdf: bytes, page_count: int, chunks: list[tuple[int, str, list[float]]]) -> int:
    # `with conn` = one transaction: if anything fails, nothing is half-saved.
    with connect() as conn:
        conn.execute("DELETE FROM documents WHERE filename = %s", (filename,))  # cascades to its chunks
        doc_id = conn.execute(
            "INSERT INTO documents (filename, pdf, page_count) VALUES (%s, %s, %s) RETURNING id",
            (filename, pdf, page_count),
        ).fetchone()["id"]
        conn.cursor().executemany(
            "INSERT INTO chunks (document_id, page_number, content, embedding) VALUES (%s, %s, %s, %s)",
            [(doc_id, page, text, Vector(embedding)) for page, text, embedding in chunks],
        )
    return doc_id


# The k chunks closest in meaning to `embedding`, best first.
# `<=>` is cosine distance (0 = same direction), so 1 - distance = similarity (1 = same meaning).
def search_chunks(embedding: list[float], k: int) -> list[dict]:
    with connect() as conn:
        return conn.execute("""
            SELECT c.id, d.id AS document_id, d.filename, c.page_number, c.content,
                   1 - (c.embedding <=> %(q)s) AS similarity
            FROM chunks c JOIN documents d ON d.id = c.document_id
            ORDER BY c.embedding <=> %(q)s
            LIMIT %(k)s
        """, {"q": Vector(embedding), "k": k}).fetchall()


# The stored PDF bytes, or None if the document doesn't exist or was uploaded before PDFs were stored.
def get_pdf(doc_id: int) -> bytes | None:
    with connect() as conn:
        row = conn.execute("SELECT pdf FROM documents WHERE id = %s", (doc_id,)).fetchone()
    return row["pdf"] if row else None


# True if a document was deleted. Its chunks go with it (ON DELETE CASCADE).
def delete_document(doc_id: int) -> bool:
    with connect() as conn:
        return conn.execute("DELETE FROM documents WHERE id = %s", (doc_id,)).rowcount == 1


# Deliberately doesn't select `pdf`: a list shouldn't carry megabytes of file data.
def list_documents() -> list[dict]:
    with connect() as conn:
        return conn.execute("""
            SELECT d.id, d.filename, d.page_count, d.uploaded_at, count(c.id) AS chunk_count
            FROM documents d LEFT JOIN chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.uploaded_at DESC
        """).fetchall()
