# Demo 1 · Using LLMs through an API

Companion to **Lecture 02 · LLM Fundamentals**. Two things live here:

1. **A notebook** that turns every sampling knob from the lecture (temperature, top-k, top-p, penalties, `max_tokens`, reasoning effort) through the OpenRouter API and shows what changes in the output, including the actual next-token distribution via `logprobs`.
2. **A tiny FastAPI app**, a joke generator, packaged with Docker. It is a template for the kind of service your group project needs: one endpoint, one LLM call, secrets in `.env`, runnable with `docker compose up`.

Everything runs on OpenRouter's **free-tier models**, so it costs nothing, at the price of rate limits (see below).

## Folder layout

```
demo1-intro-llms/
├── 01_sampling_parameters.ipynb   # the seminar notebook, executed with outputs
├── app/
│   └── main.py                    # FastAPI joke generator
├── cache/responses.json           # every API response the notebook made; re-running is free
├── requirements.txt               # shared by the notebook and the app
├── Dockerfile
├── docker-compose.yml
└── README.md
```

The `.env` file lives one level up, at the **repository root**, and is shared by all demos.

## Prerequisites

- Python 3.12 and [`uv`](https://docs.astral.sh/uv/)
- Docker Desktop (for the app; the notebook runs without it)
- An OpenRouter account and API key: <https://openrouter.ai/keys>

**Free-tier limits.** Models whose id ends in `:free` are capped at roughly 20 requests per minute and 50 per day per key (more with credits on the account). On top of that, the upstream provider of a free model can be busy and answer 429 or 502 for minutes at a time. The notebook retries with a pause when that happens; the app passes the error through to you.

## Setup

From the repository root:

```bash
cp .env.example .env          # then paste your key into API_KEY
uv venv                       # creates .venv with Python 3.12
uv pip install -r demo1-intro-llms/requirements.txt
```

`.env` is gitignored. Never commit it, never paste the key into a notebook cell.

Variables in `.env`:

| variable | meaning |
|---|---|
| `API_KEY` | your OpenRouter key |
| `BASE_URL` | `https://openrouter.ai/api/v1`, the OpenAI-compatible endpoint |
| `MODEL_NAME` | primary model, used by the app and most notebook cells |
| `SECOND_MODEL_NAME` | second model, used by the notebook cells that need `top_k`, `logprobs` or penalties |

**Why two models?** OpenRouter forwards only the parameters a provider supports and **silently drops the rest**. The primary free model accepts `temperature`, `top_p`, `seed`, `max_tokens`, `reasoning`. It does not accept `top_k`, `frequency_penalty` or `logprobs`, so a cell that sets `top_k` on it would run fine and prove nothing. The second model accepts all of those. The notebook fetches the `supported_parameters` list for both from `GET /models` and prints it, so you can see this rather than take it on faith. You can change either model in `.env`; the same check tells you which cells still work.

## The notebook

`01_sampling_parameters.ipynb` follows the lecture's pipeline: logits → temperature reshapes → a truncation knob cuts the tail → one token is sampled → repeat. It starts with one raw HTTP call so you see the wire format, then uses the `openai` SDK pointed at OpenRouter. The cells cover streaming, whether `temperature=0` is really deterministic, a temperature sweep up to 2.0, the first-token probability distribution from `logprobs`, `top_k` vs `top_p`, what happens when you combine knobs, a frequency-penalty pair, `max_tokens` truncation, and reasoning effort on vs off with the reasoning trace and its token cost.

The whole notebook makes about 21 API calls. Every response is cached in `cache/responses.json`, so re-running any cell costs nothing; set `FORCE_REFRESH = True` in the setup cell to query again. The committed notebook already contains outputs, so you can read it without a key.

To run it:

```bash
cd demo1-intro-llms
../.venv/bin/jupyter lab        # or open the folder in VS Code and pick the .venv kernel
```

## The app

`app/main.py` is a joke generator. It is prompted for *story* jokes — a character, a couple of escalating beats, a punchline in the last sentence, under 120 words — rather than one-liners, which also makes the presets below easier to tell apart. You give it a topic and a **creativity** preset; the preset is nothing more than a pair of sampling parameters:

| preset | temperature | top_p |
|---|---|---|
| `safe` | 0.3 | 0.9 |
| `normal` | 0.9 | 0.95 |
| `wild` | 1.5 | 1.0 |

Every response echoes the parameters that were actually sent, so the friendly label and the real knob sit side by side. You can override `temperature`, `top_p`, `max_tokens` and `model` per request.

Endpoints:

- `GET /health` → `{"status": "ok", "model": "<MODEL_NAME>"}`
- `POST /joke` → one joke
- `POST /joke/compare` → the same topic at all three presets, in parallel (three API calls)
- `GET /docs` → Swagger UI, the easiest way to try it

### Run locally

```bash
cd demo1-intro-llms
../.venv/bin/uvicorn app.main:app --reload
```

### Run with Docker

```bash
cd demo1-intro-llms
docker compose up --build
```

Compose reads `../.env` (see `env_file` in `docker-compose.yml`) and publishes port 8000. Open <http://localhost:8000/docs>. Stop with `docker compose down`.

### Example requests

```bash
curl -s localhost:8000/joke \
  -H "Content-Type: application/json" \
  -d '{"topic": "large language models", "audience": "CS students", "style": "pun", "creativity": "wild"}'
```

```bash
curl -s localhost:8000/joke/compare \
  -H "Content-Type: application/json" \
  -d '{"topic": "Docker"}'
```

A `/joke` response looks like:

```json
{
  "joke": "...",
  "creativity": "wild",
  "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
  "params_used": {"temperature": 1.5, "top_p": 1.0, "max_tokens": 300},
  "usage": {"prompt_tokens": 95, "completion_tokens": 160},
  "finish_reason": "stop"
}
```

`/joke/compare` returns a list of three such objects, one per preset.

Errors: an invalid body returns `422` with the validation details; a `429` from the free tier is passed through with OpenRouter's message; other provider failures return `502`.

## Reusing this for your project

Copy `app/`, `Dockerfile`, `docker-compose.yml` and `requirements.txt`, rename the endpoint, replace the system prompt. Keep the key in `.env` and keep `env_file` pointing at it; the code reads configuration from the environment and nothing else, which is what makes the same image run on your laptop and on a server.
