"""Offline integration checks: real LlamaIndex index, scripted embeddings and LLM."""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag import UNKNOWN_ANSWER, RagConfig, RagError, RagService, get_engine, load_corpus
from llama_index.core.embeddings import MockEmbedding


class CountingEmbedding(MockEmbedding):
    text_calls: int = 0

    def _get_text_embedding(self, text):
        self.text_calls += 1
        return super()._get_text_embedding(text)


class ScriptedLLM:
    def __init__(self, text="The Manila Room is an exception to isolation. [1]"):
        self.text = text
        self.prompts = []

    def complete(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(text=self.text)


class RagTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        (self.data / "documents").mkdir(parents=True)
        self.storage = self.root / "storage"
        self.doc = self.data / "documents/level-0.md"
        self.doc.write_text("# Level 0\n\nThe isolation effect separates travelers. "
                            "The Manila Room is an exception, where travelers can meet.\n")
        self.manifest = {
            "schema_version": 1,
            "documents": [{"id": "level-0", "title": "Level 0", "kind": "level",
                           "path": "documents/level-0.md",
                           "source_url": "https://backrooms-wiki.wikidot.com/level-0",
                           "authors": ["Example Author"], "license": "CC BY-SA 3.0",
                           "sha256": hashlib.sha256(self.doc.read_bytes()).hexdigest()}],
        }
        self.save_manifest()
        self.config = RagConfig(api_key="test-not-a-real-key", api_base="https://offline.invalid/v1",
                                model="offline-scripted")
        self.embedder = CountingEmbedding(embed_dim=8)
        self.llm = ScriptedLLM()

    def save_manifest(self):
        (self.data / "manifest.json").write_text(json.dumps(self.manifest))

    def service(self, **kwargs):
        return RagService(self.data, self.storage, kwargs.pop("config", self.config),
                          embed_model=kwargs.pop("embed_model", self.embedder),
                          llm=kwargs.pop("llm", self.llm), **kwargs)

    def test_browsing_needs_neither_credentials_nor_models(self):
        with patch.dict(os.environ, {}, clear=True), patch("rag._make_embedder") as embed:
            records = load_corpus(self.data)
            self.assertEqual(records[0].title, "Level 0")
            self.assertEqual(records[0].authors, ["Example Author"])
            embed.assert_not_called()
            with self.assertRaisesRegex(RagError, "API_KEY"):
                get_engine(self.data, self.storage)

    def test_prepare_persists_and_new_process_service_reuses_embeddings(self):
        service = self.service()
        service.prepare()
        self.assertGreater(self.embedder.text_calls, 0)
        self.assertEqual(self.llm.prompts, [])  # No model call during prewarming.
        second_embedder = CountingEmbedding(embed_dim=8)
        second = self.service(embed_model=second_embedder)
        second.prepare()
        self.assertEqual(second_embedder.text_calls, 0)
        self.assertEqual(len(list(self.storage.glob("index-*"))), 1)
        second.ask("Can travelers meet?")
        self.assertEqual(second_embedder.text_calls, 0)

    def test_content_and_chunk_config_invalidate_cache(self):
        self.service().prepare()
        self.doc.write_text(self.doc.read_text() + "\nAn exit leads toward Level 1.\n")
        self.manifest["documents"][0]["sha256"] = hashlib.sha256(self.doc.read_bytes()).hexdigest()
        self.save_manifest()
        fresh = CountingEmbedding(embed_dim=8)
        self.service(embed_model=fresh).prepare()
        self.assertGreater(fresh.text_calls, 0)
        third = CountingEmbedding(embed_dim=8)
        self.service(embed_model=third, config=replace(self.config, chunk_size=256)).prepare()
        self.assertGreater(third.text_calls, 0)
        self.assertEqual(len(list(self.storage.glob("index-*"))), 3)

    def test_one_grounded_generation_and_only_cited_sources(self):
        service = self.service()
        answer = service.ask("Can travelers meet on Level 0?")
        self.assertEqual(len(self.llm.prompts), 1)
        prompt = self.llm.prompts[0]
        self.assertIn("using ONLY the document passages", prompt)
        self.assertIn("not your prior knowledge", prompt)
        self.assertIn("The Manila Room is an exception", prompt)
        self.assertIn(UNKNOWN_ANSWER, prompt)
        self.assertEqual(answer.sources[0].number, 1)
        self.assertEqual(answer.sources[0].url, "https://backrooms-wiki.wikidot.com/level-0")
        self.assertEqual(answer.sources[0].title, "Level 0")
        self.assertNotIn("test-not-a-real-key", prompt)
        embedded_nodes = list(service._index.docstore.docs.values())
        self.assertIn("source_url", embedded_nodes[0].excluded_embed_metadata_keys)

    def test_abstention_and_invalid_or_missing_citations_are_not_supported_answers(self):
        for text in [UNKNOWN_ANSWER, "A fact from prior knowledge.", "Unsupported exit. [99]", ""]:
            with self.subTest(text=text):
                result = self.service(llm=ScriptedLLM(text)).ask("Which exit goes to Mars?")
                self.assertEqual(result.text, UNKNOWN_ANSWER)
                self.assertEqual(result.sources, [])

    def test_missing_retrieval_results_skips_generation(self):
        service = self.service()
        service.prepare()
        with patch.object(type(service._index), "as_retriever",
                          return_value=SimpleNamespace(retrieve=lambda _: [])):
            result = service.ask("Which exit goes to Mars?")
        self.assertEqual(result.text, UNKNOWN_ANSWER)
        self.assertEqual(self.llm.prompts, [])

    def test_model_error_is_safe_and_empty_question_does_not_prepare(self):
        service = self.service()
        with self.assertRaisesRegex(RagError, "Enter a question"):
            service.ask("   ")
        self.assertEqual(self.embedder.text_calls, 0)
        service.prepare()
        with patch.object(self.llm, "complete", side_effect=RuntimeError("API secret=test-not-a-real-key")):
            with self.assertRaises(RagError) as raised:
                service.ask("Can travelers meet?")
        self.assertNotIn("test-not-a-real-key", str(raised.exception))

    def test_rejects_missing_document_checksum_mismatch_and_path_escape(self):
        self.doc.write_text("Changed without updating the source manifest")
        with self.assertRaisesRegex(RagError, "has changed"):
            load_corpus(self.data)
        self.manifest["documents"][0]["path"] = "../../outside.md"
        self.save_manifest()
        with self.assertRaises(RagError):
            load_corpus(self.data)
        self.manifest["documents"][0]["path"] = "documents/missing.md"
        self.save_manifest()
        with self.assertRaises(RagError):
            load_corpus(self.data)

    def test_rejects_duplicate_ids_and_non_web_source_urls(self):
        self.manifest["documents"].append(dict(self.manifest["documents"][0]))
        self.save_manifest()
        with self.assertRaises(RagError):
            load_corpus(self.data)
        self.manifest["documents"].pop()
        self.manifest["documents"][0]["source_url"] = "javascript:alert(1)"
        self.save_manifest()
        with self.assertRaises(RagError):
            load_corpus(self.data)

    def test_corrupt_cache_is_rebuilt_not_loaded(self):
        self.service().prepare()
        cache = next(self.storage.glob("index-*"))
        (cache / "index_store.json").write_text("broken")
        embedder = CountingEmbedding(embed_dim=8)
        self.service(embed_model=embedder).prepare()
        self.assertGreater(embedder.text_calls, 0)
        self.assertEqual(len(list(self.storage.glob(".invalid-*"))), 1)


if __name__ == "__main__":
    unittest.main()
