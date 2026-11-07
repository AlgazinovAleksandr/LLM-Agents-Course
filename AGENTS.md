# AGENTS.md

This file is the source of truth for coding-agent instructions in this repository. `CLAUDE.md` is a relative symlink to this file for Claude Code compatibility. Edit `AGENTS.md` when updating these instructions.

## What this repository is

Teaching material for the LLM Agents course (lecturer: Aleksandr Algazinov). The course is theory-first; code here exists to *demonstrate* lecture concepts and to give students a template for their group project. Every demo must be small, readable by a student, and reproducible with a free OpenRouter key. `README.md` has the lecture plan and grading; `GROUP_PROJECT.md` has the project rules that demos should model (Dockerfile, `.env.example`, `docker compose up` instructions in the README).

## Layout conventions

- `lecture_slides/NN_topic.pdf`: lecture decks (current names use `NN_topic-with-hyphens.pdf`). Demos reference slide numbers, so check the deck before writing explanatory text. Use `pdftotext` for text and `pdftoppm` for visual inspection; some decks, including 06, have little extractable text. Keep README links and topic summaries aligned with uploaded decks; the README also retains the future lecture plan. Lecture 01 is intentionally omitted from that table.
- `demoN-topic/`: one folder per seminar, self-contained (own `README.md`, `requirements.txt`, `Dockerfile`, Compose configuration). Currently `demo1-intro-llms/` and `demo2-rag/`.
- Each demo owns its `.env` and committed `.env.example`; configuration may differ between demos. Apps load the `.env` from their demo folder; notebooks run from that folder and load `.env`; Compose uses `env_file: .env`. Keep Git ignore rules in the repository-root `.gitignore`, including `.env` and `.env.*` with an exception for `.env.example`.
- One `uv` venv at the root (`.venv`, Python 3.12), used for repository development across demos. Demo 2 also documents a local `.venv` for a standalone copy of its folder.
- `.agents/skills/` holds shared agent skills for Codex and Claude Code; `.claude/skills/*` are symlinks into it. `skills-lock.json` tracks them. Edit skills in `.agents/`.

## Commands

```bash
# environment (from repo root; install dependencies for the demo you work on)
uv venv && uv pip install -r demo1-intro-llms/requirements.txt
uv pip install -r demo2-rag/requirements-dev.txt

# demo1 notebook: execute headless from inside the demo folder (paths are relative to it)
cd demo1-intro-llms && ../.venv/bin/jupyter nbconvert --to notebook --execute --inplace 01_sampling_parameters.ipynb

# demo1 app, local
cd demo1-intro-llms && ../.venv/bin/uvicorn app.main:app --reload     # Swagger at localhost:8000/docs

# demo1 app, Docker (verified path: build, then curl /health)
cd demo1-intro-llms && docker compose up --build   # docker compose down to stop

# demo2 app, local (from repo root; create demo2-rag/.env first)
cd demo2-rag && ../.venv/bin/python -m streamlit run app.py   # localhost:8501

# demo2 app, Docker (from repo root; create demo2-rag/.env first)
cd demo2-rag && docker compose up --build -d               # localhost:8501
# from demo2-rag: download embeddings and prepare the index without generation
docker compose run --rm app python prepare.py
# stop while keeping the model cache and index volumes
docker compose down

# demo2 offline tests (from repo root; no API calls or model downloads)
cd demo2-rag && ../.venv/bin/python -m pytest tests -q
```

Demo 2 has backend and Streamlit UI tests using mock embeddings and scripted generation. Run them after changing its retrieval, persistence, corpus handling, or UI. Demo 1 has no test suite; no linter is configured. Demo 2's Dockerfile installs CPU-only Torch; see its README for the corresponding local Linux installation step.

## OpenRouter specifics that shape the code

- **Model configuration belongs to each demo.** The current `.env.example` files use Nemotron for `MODEL_NAME` and Ling for `SECOND_MODEL_NAME`. Availability, supported parameters, and free-tier limits can change. Demo 1's notebook prints `supported_parameters` from `GET /models` and uses two models because unsupported sampling parameters may be silently dropped. Check capabilities before changing a parameter demonstration; do not assume the same support across models.
- **Reasoning consumes the output budget.** Demo 1's notebook helper `generate()` sends `reasoning: {"enabled": false}` unless a cell overrides it. Its FastAPI app defaults to `low` reasoning and `max_tokens=1200`, with request overrides; it returns the reasoning trace and usage when supplied by the provider. `/joke/compare` makes three parallel generation requests.
- **Rate limits and errors.** Upstream providers can return 429 or a 200 body with an `error` object and no `choices`. The notebook's `generate()` retries with backoff on both; demo1's `app/main.py` passes only the provider's `message` through (the raw body includes the account's `user_id`). Keep error handling scoped to the implementation in each demo.
- **OpenRouter-only parameters** (`top_k`, `min_p`, `repetition_penalty`, `reasoning`) go through the OpenAI SDK's `extra_body`.

## demo1 notebook

`01_sampling_parameters.ipynb` is committed **with outputs** so students can read it without a key. Every API response is cached in `cache/responses.json`, keyed by model + messages + params + a `tag` (the tag distinguishes deliberate repeats such as the three `temperature=0` runs). Re-running makes zero calls; `FORCE_REFRESH = True` re-queries. When changing a cell's prompt or params, the old cache entry becomes dead weight: evict it so the cache holds only what the notebook shows.

## demo2 RAG app

The Backrooms Archive is a standalone Streamlit app for Lecture 06, with a question form and a document browser. It has no notebook. Keep it self-contained when copying the folder outside this repository.

- **Pipeline:** LlamaIndex `SentenceSplitter` (512-token chunks, 64-token overlap), local CPU `BAAI/bge-small-en-v1.5` embeddings, persisted vector index, top-5 retrieval, and one OpenRouter generation request per question. Questions are independent; there is no chat history or automatic fallback to `SECOND_MODEL_NAME`.
- **Initialization:** browsing documents needs neither credentials nor model initialization. Retrieval initializes the embedder; generation initializes the LLM lazily. `prepare.py` downloads the embedding model and prepares the index without generation, but still requires the API configuration in `.env`.
- **Persistence:** `storage/` is generated and ignored. The index fingerprint covers corpus text/metadata, embedding model/revision, chunk settings, and schema version. Changing the generation model does not require re-embedding. Docker volumes retain both the index and Hugging Face model cache; initial preparation needs network access.
- **Corpus:** the frozen snapshot in `data/documents/` has 50 English articles (25 levels, 15 entities, 10 objects). Preserve `data/ATTRIBUTION.md` and `data/manifest.json`, including CC BY-SA 3.0 credits and checksums. `scripts/fetch_corpus.py` is an optional deliberate refresh, never an app startup step. Raw downloads in `data/raw/` are generated and ignored; Compose mounts the bundled corpus read-only.
- **Answer checks:** citation validation checks source numbers, not factual correctness. Keep missing-information behavior and safe errors covered by offline tests; live answer quality requires a separate manual check.

## Working conventions from the course author

- The author commits; do not run `git commit`. Run the `pre-commit-scan` skill and report before they commit.
- API requests are a scarce budget. Do not make test calls; run a notebook once for its final outputs and rely on the cache. Leave quota for the author to test apps manually.
- Never print the key, headers, the client object, or `os.environ` in a notebook. The raw-HTTP cell prints the request with `Authorization: Bearer ****`.
