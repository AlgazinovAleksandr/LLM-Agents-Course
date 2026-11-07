"""UI integration checks; no embedding download or generation request."""

import hashlib
import json
import sys
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
import rag


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    documents = tmp_path / "documents"
    documents.mkdir()
    entries = []
    for identifier, title, text in [
        ("level-0", "Level 0", "# Level 0\n\nA quiet maze of yellow rooms."),
        ("object-1", "Almond Water", "# Almond Water\n\nA useful bottled drink."),
    ]:
        path = documents / f"{identifier}.md"
        path.write_text(text)
        entries.append({
            "id": identifier, "title": title,
            "kind": "level" if identifier.startswith("level") else "object",
            "path": f"documents/{identifier}.md",
            "source_url": f"https://backrooms-wiki.wikidot.com/{identifier}",
            "authors": ["Example author"], "license": "CC BY-SA 3.0",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    (tmp_path / "manifest.json").write_text(json.dumps({
        "schema_version": 1, "documents": entries,
    }))
    monkeypatch.setenv("BACKROOMS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BACKROOMS_STORAGE_DIR", str(tmp_path / "storage"))
    st.cache_resource.clear()
    yield tmp_path
    st.cache_resource.clear()


def test_document_browsing_does_not_initialize_models(corpus, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Document browsing must not initialize the answer service")
    monkeypatch.setattr(rag, "get_engine", unexpected)
    app = AppTest.from_file(str(APP_DIR / "app.py")).run(timeout=10)
    assert not app.exception
    assert len(app.tabs) == 2
    assert len(app.selectbox[0].options) == 2
    app.selectbox[0].select_index(1).run()
    assert not app.exception
    assert any("useful bottled drink" in text.value for text in app.markdown)


def test_question_displays_grounded_answer_and_source(corpus, monkeypatch):
    questions = []
    class Service:
        def ask(self, question):
            questions.append(question)
            return rag.Answer("Almond Water is a bottled drink [1].", [
                rag.Source(1, "Almond Water", "https://backrooms-wiki.wikidot.com/object-1")
            ])
    monkeypatch.setattr(rag, "get_engine", lambda *args: Service())
    app = AppTest.from_file(str(APP_DIR / "app.py")).run(timeout=10)
    app.text_input[0].input("What is Almond Water?")
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert questions == ["What is Almond Water?"]
    assert any("bottled drink [1]" in text.value for text in app.markdown)
    assert any("[1. Almond Water]" in text.value for text in app.markdown)


def test_blank_question_does_not_call_the_model(corpus, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("An empty question must not initialize the answer service")
    monkeypatch.setattr(rag, "get_engine", unexpected)
    app = AppTest.from_file(str(APP_DIR / "app.py")).run(timeout=10)
    app.button[0].click().run()
    assert not app.exception
    assert any("Enter a question" in item.value for item in app.info)
