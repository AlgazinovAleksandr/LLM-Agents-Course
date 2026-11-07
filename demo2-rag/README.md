# The Backrooms Archive

A small LlamaIndex RAG demo for Lecture 06. Browse 50 English source documents,
ask a question, and read an answer with source references. The UI has two tabs:
**Ask the archive** and **Documents**.

This folder is self-contained. Copy the entire `demo2-rag` folder anywhere;
the app does not read files from the course repository or its parent folders.
You need Docker Desktop (or Docker Engine with Compose), an internet connection,
and an OpenRouter API key.

## Run it from any folder

1. Start Docker Desktop.
2. Open a terminal inside your copied `demo2-rag` folder.
3. Create the local environment file:

   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and fill in your key:

   ```dotenv
   API_KEY='your-openrouter-api-key'
   MODEL_NAME='nvidia/nemotron-3-ultra-550b-a55b:free'
   BASE_URL='https://openrouter.ai/api/v1'
   SECOND_MODEL_NAME='inclusionai/ling-3.0-flash-vl:free'
   ```

5. Build and start the app:

   ```bash
   docker compose up --build -d
   ```

6. Open **http://localhost:8501**.

The first Docker build downloads Python packages. The first question also
downloads the embedding model and builds the document index. Prepare these
before class, without making a generation request:

```bash
docker compose run --rm app python prepare.py
```

The model cache and document index are stored in Docker volumes and reused on
later starts. Questions do not rebuild or re-embed the corpus. Answer generation
still needs OpenRouter access.

To stop the demo:

```bash
docker compose down
```

To view the server log:

```bash
docker compose logs -f app
```

## Which model does each part use?

| Part | Model / implementation | Where it runs |
|---|---|---|
| Document and question embeddings | `BAAI/bge-small-en-v1.5`, 384-dimensional English embeddings | Locally, on the container CPU |
| Splitting | LlamaIndex `SentenceSplitter`, 512-token chunks with 64-token overlap | Locally |
| Retrieval | LlamaIndex vector index; retrieve the five most similar chunks | Locally |
| Answer generation | The model in `MODEL_NAME`, through the OpenRouter-compatible endpoint in `BASE_URL` | OpenRouter |

The embedding model turns chunks and questions into vectors in the same space.
Vector similarity selects passages likely to help answer the question. We use
this small English model because the corpus and questions are English and the
demo should run on a laptop CPU. It is separate from the answer-generating LLM;
embedding the documents does not call OpenRouter. The Docker image installs a
CPU-only PyTorch wheel, so no NVIDIA GPU or CUDA setup is needed.

`SECOND_MODEL_NAME` is an optional alternate model name. The app does **not**
automatically switch models. To try the alternate, replace the value of
`MODEL_NAME` with `inclusionai/ling-3.0-flash-vl:free` in `.env`, then recreate
the app container:

```bash
docker compose up -d --force-recreate
```

Generation-model changes do not require re-embedding the documents. Free-model
availability and upstream rate limits can change; choose another model in
`MODEL_NAME` if your provider no longer serves the configured one.

## What happens when you ask a question?

```text
Markdown articles → sentence-aware chunks → local embeddings → persisted index
Question → local embedding → top 5 chunks → OpenRouter → answer + source references
```

1. The app loads the bundled Markdown documents and their source metadata.
2. Before the first question, it builds or loads a persisted LlamaIndex index.
3. It embeds your question locally and retrieves five chunks.
4. It sends those passages and your question to the configured LLM in one
   generation request. The prompt asks it to use only those passages, cite source
   numbers, and say when the answer is not in the supplied material.
5. It displays the answer and links for the sources cited. Empty responses or
   responses with missing/unknown citation numbers become a not-found answer.

Citation checks verify source numbers, not the factual correctness of every
sentence. This remains a simple baseline RAG system. Each question is independent;
the app does not add earlier answers to a conversation history.

The index is keyed by corpus contents, embedding configuration and chunking
settings. A fresh service rebuilds it if those inputs change; it otherwise
reuses saved embeddings. `prepare.py` runs the same preparation step without
asking the LLM.

## Try these questions

- What is Almond Water used for?
- How can someone leave Level 0?
- What are Hounds, and what should a traveler do when encountering one?
- Can travelers meet on Level 0?
- What did I eat for breakfast yesterday? *(Not established by this corpus.)*

These are classroom prompts, not a benchmark with a claimed accuracy score.
Compare an answer with its source document when discussing retrieval failures.

## Documents and attribution

The bundled snapshot contains **25 levels, 15 entities and 10 objects** from
the [English Backrooms Wiki](https://backrooms-wiki.wikidot.com/). It was fetched
on 6 November 2026 and converted from article HTML to Markdown. The snapshot is
fixed, so a live wiki edit does not change the demonstration unexpectedly.

Article text is **CC BY-SA 3.0**. See
[`data/ATTRIBUTION.md`](data/ATTRIBUTION.md) for source credits and
[`data/manifest.json`](data/manifest.json) for original URLs, authors, page
revisions, timestamps and file hashes. Media is excluded. Conversion removes
navigation, ratings, theme CSS and template artifacts while retaining article
text, section headings, lists, links, tabbed content and tables.

Normal use needs no scraping, wiki account, OCR, notebook, or external database.
The Markdown corpus is already included.

## Files

```text
demo2-rag/
  .env.example                 environment template; copy to .env
  .streamlit/config.toml       simple UI theme
  Dockerfile + compose.yaml   standalone local container
  requirements.txt           pinned runtime and conversion dependencies
  app.py                     document browser and question form
  rag.py                     LlamaIndex indexing, retrieval and generation
  prepare.py                 pre-download embeddings and prepare index
  data/manifest.json          source metadata and file hashes
  data/ATTRIBUTION.md         article credits and reuse terms
  data/documents/*.md         the 50 source articles
  scripts/fetch_corpus.py     optional reproducible corpus refresh
  tests/                     offline backend and UI checks
```

`.env`, local generated storage, and raw-download caches are ignored by Git and
excluded from the Docker build. The key is passed at runtime; it is not baked
into the image. The browser is bound to the local machine through port 8501.

## Optional: refresh the source snapshot

The converter uses a bounded allowlist; it does not crawl the whole wiki.
Existing raw HTML is reused unless `--refresh` is supplied. A refresh deliberately
changes the classroom snapshot, so check answers again afterward.

Normal app containers mount `data/` read-only. Run the converter with a writable
data mount, then recreate the app and prepare the updated index:

```bash
docker compose run --rm -v "$PWD/data:/app/data:rw" app python scripts/fetch_corpus.py --refresh
docker compose up -d --force-recreate
docker compose run --rm app python prepare.py
```

Keep the generated attribution and manifest with the Markdown files when moving
or distributing the demo.

## Development checks

For optional local Python development, use Python 3.12 and a virtual environment.
On Linux, install the CPU-only PyTorch wheel before the other packages, using
`pip install --no-deps torch==2.14.0+cpu --index-url https://download.pytorch.org/whl/cpu`
inside the virtual environment. On macOS the standard Torch wheel runs on CPU.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests -q
.venv/bin/python -m streamlit run app.py
```

Tests use scripted generation and mock embeddings for deterministic wiring
checks; live OpenRouter answers are a separate manual check. The backend tests
cover index reuse, cache invalidation, source numbering, missing-information
behavior, corpus validation and safe errors. UI tests cover browsing without
model initialization and submitting a question.

Verified on 6 November 2026: the Docker image built and ran on Linux ARM64 with
CPU-only PyTorch; first-run model/index preparation and persisted-volume reuse
worked; the browser returned a cited answer through the configured OpenRouter
model. All 13 offline tests (plus four subtests) passed, including when the folder
was copied outside the repository. The 50 bundled Markdown documents passed
manifest/checksum validation. The container runs as a non-root user and receives
the API key at runtime rather than from a file baked into the image.

References: [LlamaIndex](https://developers.llamaindex.ai/python/framework/),
[BGE model card](https://huggingface.co/BAAI/bge-small-en-v1.5),
[Streamlit Docker guide](https://docs.streamlit.io/deploy/tutorials/docker).
