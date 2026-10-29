# Tests for the answer step. Fakes replace retrieval and the chat model,
# so these need neither Ollama nor the database.

import pytest

from app import generate


def chunk(page: int, similarity: float) -> dict:
    return {
        "document_id": 3, "filename": "intro.pdf", "page_number": page,
        "content": f"text of page {page}", "similarity": similarity,
    }


@pytest.fixture
def fake_search(monkeypatch):
    def use(chunks):
        monkeypatch.setattr(generate.retrieve, "search", lambda question, k: chunks)
    return use


@pytest.fixture
def fake_chat(monkeypatch):
    calls = []

    def use(reply):
        def chat(system, user):
            calls.append(user)
            return reply
        monkeypatch.setattr(generate, "chat", chat)
        return calls
    return use


def test_unrelated_chunks_are_refused_without_calling_the_model(fake_search, fake_chat):
    fake_search([chunk(1, 0.55), chunk(2, 0.50)])
    calls = fake_chat("should not be used")

    result = generate.answer("How do I bake bread?")

    assert result == {"answer": generate.NOT_FOUND_ANSWER, "found": False, "sources": []}
    assert calls == []


def test_only_cited_sources_are_returned(fake_search, fake_chat):
    fake_search([chunk(4, 0.70), chunk(7, 0.65), chunk(9, 0.62)])
    fake_chat("Assignments go to Themis [2].")

    result = generate.answer("Where are assignments submitted?")

    assert result["found"] is True
    assert result["answer"] == "Assignments go to Themis [2]."
    assert result["sources"] == [{"n": 2, "document_id": 3, "filename": "intro.pdf", "page_number": 7}]


def test_made_up_citation_numbers_are_ignored(fake_search, fake_chat):
    fake_search([chunk(4, 0.70)])
    fake_chat("Something [1], and something invented [9].")

    assert [s["n"] for s in generate.answer("q")["sources"]] == [1]


def test_model_saying_not_found_is_a_refusal(fake_search, fake_chat):
    fake_search([chunk(4, 0.65)])
    fake_chat("NOT_FOUND")

    assert generate.answer("How can I secure my house?") == {
        "answer": generate.NOT_FOUND_ANSWER, "found": False, "sources": [],
    }


def test_low_scoring_chunks_are_left_out_of_the_prompt(fake_search, fake_chat):
    fake_search([chunk(4, 0.70), chunk(5, 0.40)])
    calls = fake_chat("Answer [1].")

    generate.answer("q")

    assert "page 4" in calls[0] and "page 5" not in calls[0]
