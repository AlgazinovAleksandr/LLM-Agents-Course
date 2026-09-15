"""Joke generator: a minimal FastAPI service over OpenRouter.

Demo for Lecture 02 (LLM fundamentals). The 'creativity' preset maps to sampling
parameters; every response echoes the exact parameters that were sent, so you can
see the knob behind the friendly label.

Run locally:   uvicorn app.main:app --reload
Run in Docker: docker compose up --build
Swagger UI:    http://localhost:8000/docs
"""

import asyncio
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import APIStatusError, AsyncOpenAI
from pydantic import BaseModel, Field

# Local runs pick up the repo-root .env; in Docker the same variables arrive via env_file.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_KEY = os.environ.get("API_KEY", "")
BASE_URL = os.environ.get("BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "")

if not API_KEY or not MODEL_NAME:
    raise RuntimeError("API_KEY and MODEL_NAME must be set (see .env.example)")

client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

app = FastAPI(
    title="Joke Generator",
    description="Same topic, different sampling parameters. Lecture 02 demo.",
    version="0.1.0",
)

Creativity = Literal["safe", "normal", "wild"]

PRESETS: dict[str, dict[str, float]] = {
    "safe": {"temperature": 0.3, "top_p": 0.9},
    "normal": {"temperature": 0.9, "top_p": 0.95},
    "wild": {"temperature": 1.5, "top_p": 1.0},
}

SYSTEM_PROMPT = (
    "You are a stand-up comedian who tells story jokes. Write exactly one joke about the topic "
    "the user gives, shaped as a very short story: a character in a concrete situation, two or "
    "three beats that escalate, then a punchline as the last sentence. "
    "Keep it under 120 words and stop at the punchline — never explain it. "
    "Output only the joke: no preamble, no title, no quotes."
)


class JokeRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, examples=["large language models"])
    audience: str | None = Field(None, max_length=100, examples=["computer science students"])
    style: str | None = Field(None, max_length=50, examples=["pun"])
    creativity: Creativity = Field("normal", description="Preset: safe=T0.3, normal=T0.9, wild=T1.5")
    # Raw overrides. Leave unset to use the preset.
    temperature: float | None = Field(None, ge=0, le=2)
    top_p: float | None = Field(None, gt=0, le=1)
    # A story joke runs ~160 tokens; too small a budget cuts off the punchline.
    max_tokens: int = Field(300, ge=1, le=1000)
    model: str | None = Field(
        None, description="Override MODEL_NAME for this request", examples=[MODEL_NAME]
    )


class CompareRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, examples=["large language models"])
    audience: str | None = Field(None, max_length=100)
    style: str | None = Field(None, max_length=50)
    max_tokens: int = Field(300, ge=1, le=1000)
    model: str | None = Field(None, examples=[MODEL_NAME])


class JokeResponse(BaseModel):
    joke: str
    creativity: str
    model: str
    params_used: dict[str, float | int]
    usage: dict[str, int | None]
    finish_reason: str | None


def build_prompt(topic: str, audience: str | None, style: str | None) -> str:
    parts = [f"Topic: {topic}."]
    if audience:
        parts.append(f"Audience: {audience}.")
    if style:
        parts.append(f"Style: {style}.")
    return " ".join(parts)


async def make_joke(
    prompt: str, creativity: str, params: dict[str, float | int], model: str
) -> JokeResponse:
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            **params,
        )
    except APIStatusError as e:
        # 429 from OpenRouter = free-tier rate limit; pass the status through, but only
        # the provider's message (the raw body also carries the account's user_id).
        status = e.status_code if e.status_code in (400, 401, 402, 429) else 502
        body = e.body if isinstance(e.body, dict) else {}
        message = (body.get("error") or {}).get("message") or str(e.message)
        raise HTTPException(status_code=status, detail=message) from e

    choice = resp.choices[0]
    usage = resp.usage
    return JokeResponse(
        joke=(choice.message.content or "").strip(),
        creativity=creativity,
        model=resp.model or model,
        params_used=params,
        usage={
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
        },
        finish_reason=choice.finish_reason,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/joke", response_model=JokeResponse)
async def joke(req: JokeRequest) -> JokeResponse:
    params: dict[str, float | int] = dict(PRESETS[req.creativity])
    if req.temperature is not None:
        params["temperature"] = req.temperature
    if req.top_p is not None:
        params["top_p"] = req.top_p
    params["max_tokens"] = req.max_tokens
    return await make_joke(
        build_prompt(req.topic, req.audience, req.style),
        req.creativity,
        params,
        req.model or MODEL_NAME,
    )


@app.post("/joke/compare", response_model=list[JokeResponse])
async def joke_compare(req: CompareRequest) -> list[JokeResponse]:
    """One topic, all three presets, in parallel. Three API calls."""
    prompt = build_prompt(req.topic, req.audience, req.style)
    model = req.model or MODEL_NAME
    tasks = [
        make_joke(prompt, name, {**preset, "max_tokens": req.max_tokens}, model)
        for name, preset in PRESETS.items()
    ]
    return list(await asyncio.gather(*tasks))
