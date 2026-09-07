# LLM Agents Course

**Lecturer:** Aleksandr Algazinov — https://algazinovaleksandr.github.io/

## Overview

This course is about how large language models actually work and how you can use them to build agent systems that do something useful. The course is taught bottom-up. We start with the mechanics of the model itself - tokenization, the transformer architecture, how text gets generated, and how inference works. From there we move to the agent and its parts: tools and function calling, RAG, memory and context management. Then to systems: multi-agent architectures, the framework landscape, advanced reasoning methods. And finally to practice - agentic coding, a close look at real agent systems and the evidence that they work, and what it takes to run an agent in production: evaluation, security, cost. Throughout, the emphasis is on concepts rather than on particular libraries. The frameworks in this field get updated and outdated fast. The ideas underneath them - the agent loop, the tool contract, the decision about what goes into context — do not.

## Lecture Plan

*The plan is not final: the order of topics, their composition, and how they are distributed across lectures may change.*

| # | Lecture | Topics |
|---|---|---|
| 1 | **LLM Fundamentals** | &bull; Tokenization (BPE) and word embeddings<br>&bull; How a transformer works: Q/K/V, and what attention actually computes<br>&bull; Next-token prediction — why a model does not "think", it generates<br>&bull; Generation parameters: temperature, top-p, top-k, min-p, repetition penalties |
| 2 | **LLM Inference & Serving** | &bull; Prefill and decode<br>&bull; Serving metrics: TTFT and TPOT<br>&bull; The KV cache and prefix reuse<br>&bull; Static vs. continuous batching, PagedAttention<br>&bull; Constrained decoding<br>&bull; Briefly: speculative decoding, quantization, vLLM and SGLang as serving backends |
| 3 | **Introduction to Agents** | &bull; From classical ML to LLMs to LLM agents<br>&bull; What an agent is — it need not involve an LLM at all: rule-based and RL agents<br>&bull; The anatomy of an LLM agent<br>&bull; ReAct and Plan-and-Execute<br>&bull; Build vs. adopt: write your own loop, or take an existing harness<br>&bull; When not to use an agent |
| 4 | **Agent Development Basics** | &bull; Agent tools and how to categorize them<br>&bull; Function calling end to end, and how it works under the hood<br>&bull; Skills<br>&bull; Structured output, and how it connects to constrained decoding<br>&bull; Validation and retries when the JSON comes back broken<br>&bull; Working with raw provider SDKs: see the wire format before any abstraction |
| 5 | **RAG: Basics, Practice, and Custom Retrieval** | &bull; The knowledge problem, chunking, embeddings for retrieval<br>&bull; Vector stores and ANN search, retrieve-then-generate, hybrid dense + sparse search<br>&bull; Demo: building a RAG pipeline with LlamaIndex<br>&bull; Two-stage retrieval, hard negative mining, and how to build the training set<br>&bull; Ranking features and reranking: GBDT vs. cross-encoder<br>&bull; Retrieval metrics: recall@k, MRR, nDCG |
| 6 | **Memory in Agents & Agentic RAG** | &bull; A taxonomy of memory: working, external, parametric; episodic vs. semantic<br>&bull; What to do when the context will not fit the window: map-reduce, chunk-and-summarize, hierarchical summarization, retrieval-based context selection, offloading to files<br>&bull; What to write to memory and when, and how to retrieve it; MemGPT<br>&bull; Agentic RAG: corrective, self, adaptive, multi-hop |
| 7 | **Multi-Agent Systems** | &bull; Why use more than one agent<br>&bull; Interaction patterns: sequential, orchestrator, group chat<br>&bull; Subagents: spawned by an orchestrator, each with its own isolated context<br>&bull; Shared memory and termination conditions<br>&bull; Examples from real systems |
| 8 | **Agent Frameworks Landscape** | &bull; LangChain: chains, LCEL, AgentExecutor — and the friction that produced LangGraph<br>&bull; LangGraph: graphs, state, conditional edges, checkpointers, human-in-the-loop<br>&bull; CrewAI and AutoGen<br>&bull; SGLang on the structured-execution side<br>&bull; A decision matrix, and the same task built in each |
| 9 | **Advanced Reasoning Methods** | &bull; Zero-shot and few-shot prompting<br>&bull; Chain-of-thought as a method; self-consistency<br>&bull; Tree of Thoughts, SGR<br>&bull; The generator-verifier paradigm<br>&bull; DSPy, with a demo |
| 10 | **Agentic Coding: Vibe Coding and Spec-Driven Development (Demo/Seminar)** | &bull; Vibe coding: what it is, and where it falls apart<br>&bull; Spec-driven development: spec → gate → generate → review<br>&bull; Creating and prompting agents in Claude Code; agent instruction files<br>&bull; Automating routine work; MCP, and writing your own MCP server<br>&bull; Demo: a FastAPI service built through the SDD loop |
| 11 | **Real Agent Systems: Mechanics, Evidence, Patterns** | &bull; Systems that gave us a mechanism: the memory stream and reflection in Smallville, the role pipeline in ChatDev<br>&bull; Systems with numbers behind them: SWE-bench-class coding agents, Voyager, Reflexion<br>&bull; Agent benchmarks in their own right: SWE-bench, GAIA, WebArena, OSWorld |
| 12 | **AgentOps** | &bull; Making output stable and predictable: unit tests, trajectory analysis<br>&bull; Why classical metrics (recall, precision, MSE) do not transfer to open-ended tasks<br>&bull; Task success rate, step- and trajectory-level evaluation, LLM-as-judge, pairwise comparison, human evaluation<br>&bull; Handling hallucinations; token budgeting<br>&bull; Prompt injection, direct and indirect, and the confused-deputy problem — shown side by side, insecure and hardened<br>&bull; Prompt caching and cache-aware agent design; streaming |
| 13 | **Frontiers** | &bull; The agent harness as a research frontier<br>&bull; Self-improving and self-creating agents (Ouroboros)<br>&bull; World models<br>&bull; Open research problems, and where all of this is going |

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
