# Tests for lecture summaries. Fakes replace the database, the PDF reader and the model.

from app import summarize
from app.summarize import group_pages


def words(n: int, word: str = "w") -> str:
    return " ".join([word] * n)


def test_groups_respect_the_word_limit_and_keep_page_order():
    pages = [words(5, "a"), "", words(5, "b"), words(8, "c")]

    groups = group_pages(pages, max_words=10)

    # Page 2 is empty and skipped; pages 1 + 3 fit in 10 words; page 4 starts a new group.
    assert [[page for page, _ in group] for group in groups] == [[1, 3], [4]]


def test_a_slide_longer_than_the_limit_gets_its_own_group():
    assert len(group_pages([words(20), words(2)], max_words=10)) == 2


def fake_lecture(monkeypatch, summary=None, pages=None):
    doc = {"id": 7, "filename": "crypto.pdf", "page_count": 4, "pdf": b"%PDF", "summary": summary}
    saved = {}
    calls = []

    def fake_chat(system, user):
        calls.append(system)
        return "Overview." if system == summarize.REDUCE_PROMPT else "- Point [3][99]"

    monkeypatch.setattr(summarize.db, "get_document", lambda doc_id: doc)
    monkeypatch.setattr(summarize.db, "save_summary", lambda doc_id, text: saved.update(summary=text))
    monkeypatch.setattr(summarize, "extract_pages", lambda pdf: pages or [])
    monkeypatch.setattr(summarize, "chat", fake_chat)
    return calls, saved


def test_map_then_reduce_and_the_result_is_stored(monkeypatch):
    big_slide = words(summarize.GROUP_WORDS)  # each slide fills a group: 2 groups
    calls, saved = fake_lecture(monkeypatch, pages=[big_slide, big_slide])

    result = summarize.summarize(7)

    assert calls == [summarize.MAP_PROMPT, summarize.MAP_PROMPT, summarize.REDUCE_PROMPT]
    # The overview, then the map bullets exactly as written, so their citations survive.
    assert saved["summary"] == "Overview.\n\n- Point [3][99]\n- Point [3][99]"
    # Page 99 doesn't exist in a 4-page lecture, so it's not a source.
    assert result["sources"] == [{"n": 3, "document_id": 7, "filename": "crypto.pdf", "page_number": 3}]


def test_a_one_group_lecture_skips_the_reduce_step(monkeypatch):
    calls, saved = fake_lecture(monkeypatch, pages=[words(10), words(10)])

    summarize.summarize(7)

    assert calls == [summarize.MAP_PROMPT]
    assert saved["summary"] == "- Point [3][99]"


def test_a_stored_summary_is_returned_without_calling_the_model(monkeypatch):
    calls, _ = fake_lecture(monkeypatch, summary="Cached [2]")

    result = summarize.summarize(7)

    assert calls == []
    assert result["answer"] == "Cached [2]"
    assert [s["page_number"] for s in result["sources"]] == [2]
