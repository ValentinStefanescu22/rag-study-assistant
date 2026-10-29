from app import ingest
from app.ingest import chunk_text


def test_empty_text_has_no_chunks():
    assert chunk_text("  \n ") == []


def test_short_text_is_one_chunk():
    assert chunk_text("a b c", size=5, overlap=1) == ["a b c"]


def test_chunks_overlap():
    text = " ".join(str(i) for i in range(10))  # "0 1 2 ... 9"
    assert chunk_text(text, size=4, overlap=1) == ["0 1 2 3", "3 4 5 6", "6 7 8 9"]


def test_chunks_keep_their_page_number(monkeypatch):
    # Replace the PDF reader, Ollama and the DB with fakes, so this test needs none of them.
    monkeypatch.setattr(ingest, "extract_pages", lambda _: ["intro", "", "normal forms"])
    monkeypatch.setattr(ingest, "embed_documents", lambda texts: [[0.0] * 768 for _ in texts])
    saved = []

    def fake_save_document(filename, page_count, chunks):
        saved.extend(chunks)
        return 1

    monkeypatch.setattr(ingest.db, "save_document", fake_save_document)

    result = ingest.ingest_pdf("db.pdf", b"")

    assert result == {"id": 1, "filename": "db.pdf", "pages": 3, "chunks": 2}
    # Page 2 was empty, so it produced no chunk, and page 3 is still labelled 3.
    assert [(page, text) for page, text, _ in saved] == [(1, "intro"), (3, "normal forms")]
