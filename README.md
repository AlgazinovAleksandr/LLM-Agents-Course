# LLM Agents Course

**Lecturer:** Aleksandr Algazinov — https://algazinovaleksandr.github.io/

## Overview

This course is about how large language models actually work and how you can use them to build agent systems that do something useful. The course is taught bottom-up. We start with the mechanics of the model itself - tokenization, the transformer architecture, how text gets generated, and how inference works. From there we move to the agent and its parts: tools and function calling, RAG, memory and context management. Then to systems: multi-agent architectures, the framework landscape, advanced reasoning methods. And finally to practice - agentic coding, a close look at real agent systems and the evidence that they work, and what it takes to run an agent in production: evaluation, security, cost. We close on the open research frontier. Throughout, the emphasis is on concepts rather than on particular libraries. The frameworks in this field get updated and outdated fast. The ideas underneath them - the agent loop, the tool contract, the decision about what goes into context — do not.

## Lecture Plan

*The plan is not final: the order of topics, their composition, and how they are distributed across lectures may change.*

Slides are in [`lecture_slides/`](lecture_slides/) and are added as lectures are delivered. The numbers in the table match the file names.

| # | Lecture | Topics |
|---|---|---|
| 00 | **[Course Introduction](lecture_slides/00_course-introduction.pdf)** | &bull; The agent harness as the motivating example<br>&bull; Six waves of agent development<br>&bull; Breaking a harness down into the building blocks this course teaches<br>&bull; The course arc, the group project, and grading |
| 02 | **[LLM Fundamentals](lecture_slides/02_llm-fundamentals.pdf)** | &bull; Tokenization (BPE) and word embeddings<br>&bull; How a transformer works: Q/K/V, and what attention actually computes<br>&bull; Next-token prediction — why a model does not "think", it generates<br>&bull; Generation parameters: temperature, top-p, top-k, min-p, repetition penalties<br>&bull; Determinism and seeds<br>&bull; Reasoning effort as a generation knob |
| 03 | **[LLM Inference & Serving](lecture_slides/03_llm-inference-and-serving.pdf)** | &bull; Prefill and decode; serving metrics TTFT and TPOT<br>&bull; The KV cache and prefix reuse<br>&bull; Static vs. continuous batching, PagedAttention<br>&bull; Constrained decoding<br>&bull; From weights to an endpoint: quantization (GGUF, GPTQ, AWQ), vLLM vs. SGLang, latency triage<br>&bull; Briefly: speculative decoding |
| 04 | **[Introduction to Agents](lecture_slides/04_introduction-to-agents.pdf)** | &bull; From classical ML to LLMs to LLM agents: control vs. universality<br>&bull; What an agent is — it need not involve an LLM at all: rule-based and RL agents, autonomy as a scale<br>&bull; The anatomy of an LLM agent, and termination: the part you have to write<br>&bull; Workflow vs. agent: routing, reflection, orchestrator–worker, ReAct, Plan-and-Execute<br>&bull; Build vs. adopt: write your own loop, or take an existing harness<br>&bull; Human-in-the-loop as architecture; when not to use an agent |
| 05 | **Agent Development Basics** | &bull; Agent tools and how to categorize them<br>&bull; Function calling end to end, and how it works under the hood<br>&bull; Skills, and how a harness discovers them<br>&bull; Structured output and constrained decoding; validation and retries when the JSON comes back broken<br>&bull; Timeouts, rate limits, cost accounting, idempotency for side-effecting tools<br>&bull; Computer-use and browser agents<br>&bull; Working with raw provider SDKs: see the wire format before any abstraction |
| 06 | **RAG: Basics, Practice, and Custom Retrieval** | &bull; The knowledge problem, chunking, contextual retrieval, embeddings for retrieval<br>&bull; Vector stores and ANN search, retrieve-then-generate, hybrid dense + sparse search with rank fusion<br>&bull; Demo: building a RAG pipeline with LlamaIndex<br>&bull; Two-stage retrieval, hard negative mining, and how to build the training set<br>&bull; Ranking features and reranking: GBDT vs. cross-encoder<br>&bull; Retrieval metrics: recall@k, MRR, nDCG |
| 07 | **Memory in Agents & Agentic RAG** | &bull; The model's side of the window: extending and shrinking context (RoPE scaling, KV eviction, prompt compression)<br>&bull; A taxonomy of memory: working, external, parametric; episodic vs. semantic<br>&bull; What to do when the context will not fit the window: map-reduce, hierarchical summarization, retrieval-based context selection, offloading to files<br>&bull; What to write to memory and when, how to update and retrieve it; Smallville's memory stream, MemGPT<br>&bull; How a production harness compacts context; advertised vs. effective context length<br>&bull; Agentic RAG: corrective, self, adaptive, multi-hop |
| 08 | **Multi-Agent Systems** | &bull; Why use more than one agent<br>&bull; Interaction patterns: sequential, orchestrator, group chat<br>&bull; Subagents: spawned by an orchestrator, each with its own isolated context<br>&bull; Shared memory<br>&bull; Termination, liveness, and deadlock<br>&bull; Examples from real systems; the router need not be an LLM |
| 09 | **Agent Frameworks Landscape** | &bull; LangChain: chains, LCEL, AgentExecutor — and the friction that produced LangGraph<br>&bull; LangGraph: graphs, state, conditional edges, checkpointers, human-in-the-loop, unattended runs<br>&bull; Deep Agents, CrewAI, AutoGen and Microsoft Agent Framework<br>&bull; SGLang on the structured-execution side<br>&bull; A2A and agent standards; hosted agent runtimes<br>&bull; A decision matrix, and the same task built in several frameworks |
| 10 | **Advanced Reasoning Methods** | &bull; Zero-shot and few-shot prompting<br>&bull; Chain-of-thought as a method; self-consistency<br>&bull; Tree of Thoughts, SGR<br>&bull; The generator-verifier paradigm<br>&bull; DSPy, with a demo |
| 11 | **[Agentic Coding: From Vibe Coding to Agentic Engineering](lecture_slides/11_agentic-coding.pdf)** | &bull; Vibe coding vs. agentic engineering; is writing code really the bottleneck?<br>&bull; Instruction files, skills, and context hygiene in a coding agent<br>&bull; Permission modes, hooks, guardrails, and sandboxing<br>&bull; Extending the harness: skills vs. plugins vs. MCP<br>&bull; Spec-driven development, and TDD as a way to steer a coding agent<br>&bull; Independent review: cross-model review, CI/CD with GitHub Actions<br>&bull; Followed by a hands-on session: a project built end to end with a coding agent |
| 12 | **Real Agent Systems: Mechanics, Evidence, Patterns** | &bull; Systems that gave us a mechanism: the role pipeline in ChatDev, deep-research agents, persistent personal agents<br>&bull; Systems with numbers behind them: SWE-bench-class coding agents, Voyager, Reflexion<br>&bull; Agent benchmarks in their own right: SWE-bench, GAIA, WebArena, OSWorld, τ-bench — and why a score means nothing without its harness<br>&bull; The binding constraint: model vs. harness vs. operator |
| 13 | **AgentOps** | &bull; Making output stable and predictable: unit tests, trajectory analysis<br>&bull; Why classical metrics (recall, precision, MSE) do not transfer to open-ended tasks<br>&bull; Task success rate, step- and trajectory-level evaluation, LLM-as-judge, pairwise comparison, human evaluation<br>&bull; Handling hallucinations; token budgeting<br>&bull; Prompt injection, direct and indirect, and the confused-deputy problem — shown side by side, insecure and hardened<br>&bull; Prompt caching and cache-aware agent design; streaming<br>&bull; Scheduling and running agents unattended |
| 14 | **Frontiers** | &bull; The agent harness as a research frontier<br>&bull; Self-improving and self-creating agents (Ouroboros)<br>&bull; World models, and the case against LLMs<br>&bull; Is AGI the goal?<br>&bull; What becomes scarce for humans |

## Seminars and Demos

Each seminar lives in its own folder with a README that covers setup and how to run it. All demos use [OpenRouter](https://openrouter.ai) with free-tier models, so a free key is enough; the `.env.example` at the repository root lists the variables every demo reads.

| # | Folder | Lecture | What is inside |
|---|---|---|---|
| 1 | [demo1-intro-llms](demo1-intro-llms/) | 02 · LLM Fundamentals | &bull; A notebook that turns every generation parameter through the API — temperature, top-k, top-p, penalties, `max_tokens`, reasoning effort — and shows the next-token distribution via `logprobs`<br>&bull; A minimal FastAPI service (a joke generator with creativity presets) packaged with Docker, as a template for the group project |

## Grading

**Grade = 0.4 × project proposal + 0.6 × final defense**

Projects are done in teams of four. Each stage is marked out of 10. The full rules — teams, repository requirements, presentation format, attendance — are in [GROUP_PROJECT.md](GROUP_PROJECT.md).

### Project Proposal — 10 points

- **4** — an idea that actually makes sense: what problem it solves, and why it needs an LLM
- **4** — a working MVP: 1 point for running live, 1 for a clean and well-organized repository, 2 for the core LLM feature
- **2** — answers to technical questions

### Final Defense — 10 points

- **4** — finished: 2 points for being deployed on a server and reachable by link, 2 for matching what you proposed
- **4** — tooling and technical depth
- **2** — answers to technical questions

### What "Technical Depth" Means

This is not a race for complexity. A project with clean, well-structured code and a substantial idea behind it loses nothing for skipping function calling, say — *as long as you can explain why you did not need it*. Make that case in your presentation or in your answers to questions, and it counts.
