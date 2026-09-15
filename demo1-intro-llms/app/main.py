"""Joke generator: a minimal FastAPI service over OpenRouter.

Demo for Lecture 02 (LLM fundamentals). The 'creativity' preset maps to sampling
parameters; every response echoes the exact parameters that were sent, so you can
see the knob behind the friendly label. Reasoning is on at 'low' effort by default,
so each response also carries the model's thinking trace and what it cost in tokens.

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
    description=(
        "Same topic, different sampling parameters, with the model's reasoning trace. "
        "Lecture 02 demo."
    ),
    version="0.1.0",
)

Creativity = Literal["safe", "normal", "wild"]
Reasoning = Literal["off", "low", "medium", "high"]

# Reasoning tokens are emitted before the answer and billed as output, so they come out
# of the same max_tokens budget: too small a budget and the thinking eats the punchline.
DEFAULT_REASONING: Reasoning = "low"

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
    reasoning: Reasoning = Field(
        DEFAULT_REASONING, description="Thinking effort before the answer; 'off' disables it"
    )
    # A story joke runs ~160 tokens, the thinking at 'low' effort a few hundred more;
    # too small a budget cuts off the punchline (finish_reason becomes 'length').
    max_tokens: int = Field(1200, ge=1, le=4000)
    model: str | None = Field(
        None, description="Override MODEL_NAME for this request", examples=[MODEL_NAME]
    )


class CompareRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, examples=["large language models"])
    audience: str | None = Field(None, max_length=100)
    style: str | None = Field(None, max_length=50)
    reasoning: Reasoning = Field(DEFAULT_REASONING)
    max_tokens: int = Field(1200, ge=1, le=4000)
    model: str | None = Field(None, examples=[MODEL_NAME])


class JokeResponse(BaseModel):
    joke: str
    reasoning: str | None = Field(
        None, description="The thinking trace, when reasoning is on and the provider returns it"
    )
    creativity: str
    model: str
    params_used: dict[str, float | int | str]
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
    prompt: str, creativity: str, params: dict[str, float | int], model: str, reasoning: str
) -> JokeResponse:
    # `reasoning` is an OpenRouter extension rather than an OpenAI parameter, so it
    # travels in extra_body. {"enabled": False} is how you turn a thinking model off.
    effort = {"enabled": False} if reasoning == "off" else {"effort": reasoning}
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            extra_body={"reasoning": effort},
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
    # The trace and its token count are not OpenAI fields either; the SDK parks unknown
    # keys in model_extra, and a provider may leave them out even with reasoning on.
    trace = (choice.message.model_extra or {}).get("reasoning")
    token_details = getattr(usage, "completion_tokens_details", None) if usage else None
    return JokeResponse(
        joke=(choice.message.content or "").strip(),
        reasoning=(trace or "").strip() or None,
        creativity=creativity,
        model=resp.model or model,
        params_used={**params, "reasoning": reasoning},
        usage={
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
            "reasoning_tokens": getattr(token_details, "reasoning_tokens", None),
        },
        finish_reason=choice.finish_reason,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL_NAME, "reasoning": DEFAULT_REASONING}


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
        req.reasoning,
    )


@app.post("/joke/compare", response_model=list[JokeResponse])
async def joke_compare(req: CompareRequest) -> list[JokeResponse]:
    """One topic, all three presets, in parallel. Three API calls."""
    prompt = build_prompt(req.topic, req.audience, req.style)
    model = req.model or MODEL_NAME
    tasks = [
        make_joke(prompt, name, {**preset, "max_tokens": req.max_tokens}, model, req.reasoning)
        for name, preset in PRESETS.items()
    ]
    return list(await asyncio.gather(*tasks))
