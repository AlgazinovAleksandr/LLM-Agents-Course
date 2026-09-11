# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Teaching material for the LLM Agents course (lecturer: Aleksandr Algazinov). The course is theory-first; code here exists to *demonstrate* lecture concepts and to give students a template for their group project. Every demo must be small, readable by a student, and reproducible with a free OpenRouter key. `README.md` has the lecture plan and grading; `GROUP_PROJECT.md` has the project rules that demos should model (Dockerfile, `.env.example`, `docker compose up` instructions in the README).

## Layout conventions

- `lecture_slides/NN_topic.pdf`: lecture decks. Demos reference slide numbers, so check the deck (`pdftotext` / `pdftoppm` work) before writing explanatory text.
- `demoN-topic/`: one folder per seminar, self-contained (own `README.md`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`). Currently only `demo1-intro-llms/`.
- One `.env` at the **repository root**, shared by all demos and gitignored. `.env.example` lists the variables: `API_KEY`, `BASE_URL` (OpenRouter), `MODEL_NAME`, `SECOND_MODEL_NAME`. Demos load it as `../.env` (notebooks via `load_dotenv`, compose via `env_file: ../.env`).
- One `uv` venv at the root (`.venv`, Python 3.12), used by every demo.
- `.agents/skills/` holds Claude Code skills; `.claude/skills/*` are symlinks into it. `skills-lock.json` tracks them. Edit skills in `.agents/`.

## Commands

```bash
# environment (from repo root)
uv venv && uv pip install -r demo1-intro-llms/requirements.txt

# demo1 notebook: execute headless from inside the demo folder (paths are relative to it)
cd demo1-intro-llms && ../.venv/bin/jupyter nbconvert --to notebook --execute --inplace 01_sampling_parameters.ipynb

# demo1 app, local
cd demo1-intro-llms && ../.venv/bin/uvicorn app.main:app --reload     # Swagger at localhost:8000/docs

# demo1 app, Docker (verified path: build, then curl /health)
cd demo1-intro-llms && docker compose up --build   # docker compose down to stop
```

There is no test suite and no linter configured.

## OpenRouter specifics that shape the code

- **Free models silently drop unsupported parameters.** `MODEL_NAME` (Nemotron free) accepts only `temperature`, `top_p`, `seed`, `max_tokens`, `reasoning`. `SECOND_MODEL_NAME` (Ling free) additionally accepts `top_k`, penalties, `logprobs`. This is why the notebook uses two models and prints `supported_parameters` from `GET /models` before any call. Check that endpoint before proposing a parameter demo on a given model.
- **Both free models think by default.** Reasoning tokens eat the `max_tokens` budget and the visible answer comes back empty. The notebook helper `generate()` sends `reasoning: {"enabled": false}` unless a cell overrides it; the app does not enable reasoning.
- **Rate limits.** Free tier is ~20 requests/min and ~50/day per key, and upstream providers return 429 or a 200 body with an `error` object and no `choices` when busy. `generate()` retries with backoff on both; `app/main.py` passes only the provider's `message` through (the raw body includes the account's `user_id`).
- **OpenRouter-only parameters** (`top_k`, `min_p`, `repetition_penalty`, `reasoning`) go through the OpenAI SDK's `extra_body`.

## demo1 notebook

`01_sampling_parameters.ipynb` is committed **with outputs** so students can read it without a key. Every API response is cached in `cache/responses.json`, keyed by model + messages + params + a `tag` (the tag distinguishes deliberate repeats such as the three `temperature=0` runs). Re-running makes zero calls; `FORCE_REFRESH = True` re-queries. When changing a cell's prompt or params, the old cache entry becomes dead weight: evict it so the cache holds only what the notebook shows.

## Working conventions from the course author

- The author commits; do not run `git commit`. Run the `pre-commit-scan` skill and report before they commit.
- API requests are a scarce budget. Do not make test calls; run a notebook once for its final outputs and rely on the cache. Leave quota for the author to test apps manually.
- Never print the key, headers, the client object, or `os.environ` in a notebook. The raw-HTTP cell prints the request with `Authorization: Bearer ****`.
