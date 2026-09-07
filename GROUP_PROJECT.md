# Group Project

The project is the whole of your grade for this course. It runs in two stages - a **project proposal** partway through, and a **final defense** at the end. Each is marked out of 10.

**Grade = 0.4 × project proposal + 0.6 × final defense**

This document is the full set of rules. If something here is unclear, ask before the deadline rather than after it.

## Teams

Projects are done in **teams of four**.

- Fewer than four is possible only after discussing it with me, and only in exceptional cases.
- More than four is not possible.

Register your team in the Google table linked in the group chat.

## Dates

Deadlines and defense dates are announced in the group chat.

## The Repository

Your work lives in a GitHub repository. Requirements:

- **Visibility** — the repository must be public, or you must add me as a collaborator. **Public is strongly preferred.**
- **Created no earlier than September 2026.** If you want to build on a project you have done before, fork it and start from a new repository - do not continue in the old one.
- **README in English or Russian.** Either is fine.

The repository must be in good shape. Concretely, it should contain:

- A **`Dockerfile`**.
- A **`.env.example`** listing every environment variable the project needs, with placeholder values.
- **Docker launch instructions in the README** — the exact command, e.g. `docker compose up`, and anything that has to happen before it.
- **The full name and GitHub nickname of every team member.**
- **An explanation of the LLM in the README** — which provider and model you use, what the model actually does in your project, and what for.
- **A repository someone else can navigate** — a sensible structure and file names that say what the file is. Nothing in it should be there by accident: no abandoned drafts, no dead code someone forgot to delete. Experiment, evaluation, and data-exploration notebooks are welcome — that work is part of the project.

## The Presentation

You present the project at both stages. Roughly 20 minutes each:

| Stage | Presentation | Questions | My comments |
|---|---|---|---|
| Project proposal | 10 min | 8 min | 2 min |
| Final defense | 12 min | 8 min | — |

Slight variation is possible.

## Grading

Points **1–8 of each stage are the team's** - everyone on the team gets the same result. The **2 points for answering technical questions are individual**: they are yours alone, and they depend on how you personally answer.

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

## The One Blocker

The **4 points for the idea at the project proposal are all-or-nothing — 0 or 4, nothing in between.** This is the only blocker in the course; nothing else can stop you.

The bar is deliberately low. The idea does not have to be original, ambitious, or even good. It has to **make sense** - a real problem, and a reason an LLM belongs in the solution. I do not expect anyone to fail this.

If it does happen:

- You present the new idea.
- Once the new idea is accepted, the 4 points are **not** restored. They stay lost for the proposal stage.
- Everything else is untouched. The MVP points you earned at the proposal stand as graded, your question points stand, and you go on to the final defense as normal.

## What You Will Be Asked

Four kinds of questions.

**The idea and the motivation of the project.** You need to understand what you are builing and what for

**Your design decisions.** Why these tools, why these concepts — and why not the obvious alternatives. I want to hear, in technical terms, why the project is built this way and not another way. Being able to say why you *did not* do something counts for as much as what you did.

**The code.** Why does this file exist? What does this script do?

**Lecture material.** At the project proposal, everything covered before it. At the final defense, the whole course.

## Defending Early

You may present either stage ahead of schedule. The range of questions does not shrink if you do:

- An early **final defense** still covers the entire course.
- An early **project proposal** still covers everything scheduled to be covered before the official proposal date — including lectures that have not been delivered yet.

Everyone is examined on the same material, whenever they present.

## Attendance

**Every team member attends both the project proposal and the final defense.** The only excuse is a medical one, and it needs a doctor's note.

- **Missed one stage, with a note** — your answers at the stage you did attend set your question score for both. The same result is written twice. This works in either direction: miss the proposal and the final defense covers both; miss the final defense and the proposal covers both.
- **Missed both stages** — 0 for all question points, automatically. A doctor's note does not change this (keep in mind that you still get the team points).
- **Attended but did not participate in the presentation** — at most 1 of the 2 question points for that stage, no matter how well you answer.

Defenses are held online, so who speaks is easy to check. **Presenting at least one slide counts as participating** — every team member is expected to do at least that.

## Office Hours

There will be **at least two office hours** — one about two to three weeks before the project proposal, and another the same distance before the final defense. Bring your idea, your architecture, or whatever is currently stuck. Times are announced in the group chat.

## Research Projects

If you want to do a research project rather than a product, discuss the idea with me in advance. On top of the presentation, I will require an arXiv paper at minimum.

## Before You Defend

- [ ] Team registered in the Google table
- [ ] Repository is public, or I am a collaborator
- [ ] Repository created no earlier than September 2026 (forked, if based on earlier work)
- [ ] `Dockerfile` present
- [ ] `.env.example` present
- [ ] README explains how to launch with Docker
- [ ] README explains which LLM provider and model you use, and what for
- [ ] README lists every member's full name and GitHub nickname
- [ ] Project is deployed and reachable by link *(final defense — optional, see below)*
- [ ] Every team member will be present, and every team member will present at least one slide

Deployment is the one item on this list you may deliberately skip. It is worth 2 of the 10 points at the final defense, and if your team decides those 2 points are not worth the effort, that is totally fine.
