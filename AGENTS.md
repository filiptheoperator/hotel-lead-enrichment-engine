# HOTEL AI DISCOVERY — AGENT INSTRUCTIONS

## Role of this repository
This repository is the **technical execution layer for the Lead Engine** of The Hotel Operator / Hotel AI Discovery phase. It is not the canonical business knowledge base and must not become a competing CRM or research store.

## Canonical truth
Google Drive is the canonical source of truth for business requirements, Market Research, Lead Engine records, Discovery Command Center, decisions and active system manifests.

Exact Drive IDs and current manifest version must be supplied in the execution handoff. **Do not commit private Drive IDs, lead data, community data, credentials or internal hotel information to this public repository.**

## Current business phase
DISCOVERY.

The objective is to:
1. understand recurring hospitality pains and what works/fails;
2. discover and enrich high-fit hotel/person leads;
3. support evidence-based outreach and discovery conversations;
4. feed learnings back into the canonical Market Research and Lead Engine;
5. only later turn validated repeated pains into service hypotheses/products.

Primary segment: independent / boutique / small-to-medium 3–4 star hotels. Adjacent hospitality segments may be retained when relevant.

## Repository scope
Use this codebase for repeatable technical work such as:
- ingest/normalization;
- hotel and person entity resolution;
- enrichment;
- scoring and prioritization;
- QA and run manifests;
- approved public-source collection pipelines;
- export/sync adapters for the canonical structured store;
- outreach **draft generation**, never automatic sending unless a later explicit human-approved system contract permits it.

## Non-negotiable rules
- Raw inputs are immutable.
- Unknown values remain unknown; never fabricate enrichment.
- Every consequential enriched field should retain source/provenance where practical.
- Do not scrape sources whose terms prohibit automated collection or where authorization is unclear.
- Do not store sensitive personal data, guest PII, credentials or private hotel secrets.
- Do not send cold email, DMs or other outbound communication from code without an explicit human gate.
- A contact is not a qualified lead by itself. Qualification requires context/evidence, a problem or conversation reason, and a next-action hypothesis.
- Keep code/config changes minimal and testable.

## Data contract alignment
Technical outputs must map cleanly to the canonical conceptual entities:
- Hotel
- Person
- Opportunity
- Outreach Queue
- Contact History
- Enrichment Queue

Market patterns and service hypotheses remain business-layer objects and should not be redefined in code without an explicit schema change handoff.

## Tool division
- ChatGPT: control plane, architecture, synthesis, Drive/Sheets governance and QA.
- GPT Work: browser-heavy permitted research/enrichment.
- Codex / Claude Code: this repository, scripts, tests, data pipelines and backend work.
- VS Code: local development/review surface.
- GitHub: source of truth for code and versioned technical configuration only.

## Before substantial work
Require an execution handoff containing:
- objective;
- current active manifest reference/version;
- input source;
- allowed/forbidden actions;
- output schema;
- completion criteria;
- write-back destination.

If those are missing and materially affect correctness, inspect the current project handoff/context before changing code rather than inventing architecture.
