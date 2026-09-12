# HOTEL AI DISCOVERY — Discovery Data Engine

Technical backend for **The Hotel Operator** — https://thehoteloperator.com/

This repository is the canonical **codebase** for the HOTEL AI DISCOVERY backend. It supports evidence-first hotel intelligence, lead discovery, enrichment, entity resolution, scoring, QA and future approved automation.

## Authority model

- **Google Drive / Google Sheets** = canonical business knowledge, evidence, structured masters, active manifests, run contracts and decisions.
- **This GitHub repository** = canonical code, tests, technical configuration and version history for the Discovery backend.
- **VS Code** = local development/execution surface.
- **Codex** = primary technical implementation agent.
- **Claude Code** = secondary technical architect/challenger and approved implementation agent for repo-scale work.

This public repository must never become a second business knowledge base. Do not commit private Drive IDs, lead/community datasets, confidential hotel data, guest PII, credentials or private employment information.

## Current business phase

**DISCOVERY**.

The goal is not to prematurely productize a service. The system exists to:

1. understand recurring hotel-market problems;
2. build qualified Hotel Intelligence and Lead Engine records;
3. normalize permitted Community Intelligence;
4. support Competitor Intelligence and gap analysis;
5. prepare high-quality discovery conversations;
6. return real learning to the canonical business system.

Primary target: independent / boutique / small-to-medium **3–4 star hotels**. This is a priority, not an exclusion rule.

## Canonical source domains

The backend must keep these source domains distinct:

- **Community Intelligence** — permitted community sources, threads, contributions, people and community signals.
- **Hotel Intelligence** — canonical real-hotel entities, hotel-side people, observable tech stack, pains, triggers and opportunities.
- **Competitor Intelligence** — target/peer sets, atomic observations, benchmarks and opportunity gaps.

They feed normalized **Market Research + Lead Engine**, which feed the **Discovery Command Center**.

## Existing working pipeline

The repository already contains a useful Python-first enrichment pipeline:

`raw ingest -> normalize -> score -> enrich -> drafts/exports -> QA -> run summary`

Reusable strengths already present include:

- normalization and scoring;
- enrichment;
- source attribution;
- QA and run summaries;
- configuration separated from code;
- run-to-run delta reporting;
- draft generation;
- deterministic local execution.

### Legacy adapters

`ClickUp export`, Make provisioning and older city/batch assumptions are **legacy/optional technical adapters**, not the current business source-of-truth model. They may be reused only when an active HOTEL AI DISCOVERY run explicitly calls for them.

The planned future sales CRM is **HubSpot**, and only for curated qualified companies/contacts/deals/activity after the Phase-2 gate. Raw research does not move into HubSpot.

## Active technical roadmap

The current technical run is **TECH_RUN_01 — Discovery Backend Foundation**. Its implementation priorities are:

1. versioned data contracts for Community / Hotel / Competitor Intelligence;
2. exact-ID, read-only Google Drive registry/mirror;
3. canonical Sheet adapters;
4. deterministic entity resolution and deduplication;
5. evidence/provenance validation;
6. config-driven explainable scoring;
7. run state, audit log and QA;
8. dry-run write-back diff;
9. allowlisted/idempotent Sheets write-back only after dry-run validation;
10. tests and current operator documentation.

Full CRM automation, dashboard polish and live HubSpot synchronization remain Phase 2.

## Non-negotiable data rules

- raw inputs are immutable;
- unknown values remain unknown;
- `NOT_OBSERVED` is not `ABSENT_VERIFIED`;
- inferred values must be labeled;
- consequential derived fields should preserve provenance where practical;
- uncertain entities are not silently merged;
- prohibited/unauthorized scraping is not implemented;
- outbound email/DM/calls are not automatically sent;
- a contact alone is not a qualified lead.

A useful opportunity explains **who/which hotel, evidence/context, problem/reason, why now, possible value, confidence and next action**.

## Repository structure

Current legacy + active structure includes:

- `configs/` — project/scoring/enrichment/QA technical configuration
- `data/` — ignored runtime inputs and derived working data
- `docs/` — technical/operator documentation
- `outputs/` — generated runtime artifacts
- `prompts/` — technical prompt assets
- `src/` — pipeline, QA, reporting and orchestration code
- `AGENTS.md` — Codex/agent instructions
- `CLAUDE.md` — Claude Code instructions

As TECH_RUN_01 progresses, prefer modular boundaries such as `connectors/drive`, `contracts`, `ingest`, `normalize`, `entities`, `evidence`, `scoring`, `qa`, `writeback`, `reporting` and `cli` without rewriting working code unnecessarily.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Populate secrets and runtime canonical IDs **locally only**.

Run tests before substantive changes:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

The historical demo command is:

```bash
python3 src/main.py
```

Use it only while it remains valid on the current branch and after reviewing the current docs/configs.

## Agent workflow

Before substantial work, the handoff must identify:

- current active HOTEL AI DISCOVERY manifest/version;
- phase;
- relevant RUN / TECH_RUN contract;
- input source;
- allowed/forbidden actions;
- output schema;
- completion criteria;
- canonical write-back destination.

Read `AGENTS.md`, `CLAUDE.md` and `docs/` before repo-scale changes.

## Related repositories

- `filiptheoperator/hotel-ai-clarity` — The Hotel Operator website / public positioning.
- `filiptheoperator/filip-ai-os` — separate personal OS; donor for exact-ID Drive/security patterns only.
- `filiptheoperator/codex_acquisition_orchestrator` — legacy acquisition donor; not active architecture.
- `filiptheoperator/hotel-aios-kitchen-demo` — historical UI/Hotel AIOS donor.

See `docs/BUSINESS_CONTEXT.md`, `docs/BACKEND_ROADMAP.md` and `docs/VS_CODE_SETUP.md` for the public-safe operating context.