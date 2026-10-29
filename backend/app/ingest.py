# Ingestion: PDF bytes -> pages -> chunks -> embeddings -> database.

from io import BytesIO

from pypdf import PdfReader

from app import db
from app.providers import embed_documents

CHUNK_WORDS = 250    # ~330 tokens: small enough to be about one idea
OVERLAP_WORDS = 50   # repeated between neighbours so an idea isn't cut in half
EMBED_BATCH = 32     # chunks sent to Ollama per request


# One string per page. Scanned (image-only) pages come back empty.
def extract_pages(pdf_bytes: bytes) -> list[str]:
    reader = PdfReader(BytesIO(pdf_bytes))
    return [page.extract_text() or "" for page in reader.pages]


# Split text into windows of `size` words, each starting `size - overlap` words after the last.
def chunk_text(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    words = text.split()  # also collapses the messy whitespace PDFs produce
    chunks = []
    start = 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
        start += size - overlap
    return chunks


def ingest_pdf(filename: str, pdf_bytes: bytes) -> dict:
    pages = extract_pages(pdf_bytes)

    # Chunk each page separately so every chunk knows its exact page number (for citations).
    # ponytail: a sentence split across two pages lands in two chunks; fine for slides/lecture notes.
    pieces = [
        (page_number, chunk)
        for page_number, text in enumerate(pages, start=1)
        for chunk in chunk_text(text)
    ]
    if not pieces:
        raise ValueError("No text found in this PDF. Is it a scanned image?")

    vectors = []
    for i in range(0, len(pieces), EMBED_BATCH):
        batch = pieces[i:i + EMBED_BATCH]
        vectors += embed_documents([text for _, text in batch])

    doc_id = db.save_document(
        filename,
        pdf_bytes,
        len(pages),
        [(page, text, vector) for (page, text), vector in zip(pieces, vectors)],
    )
    return {"id": doc_id, "filename": filename, "pages": len(pages), "chunks": len(pieces)}
