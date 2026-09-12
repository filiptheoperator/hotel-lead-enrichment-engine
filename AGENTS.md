# HOTEL AI DISCOVERY — AGENT INSTRUCTIONS

## Role of this repository
This repository is the **technical execution layer for the Lead Engine and future Discovery automation** of The Hotel Operator / Hotel AI. It is not the canonical business knowledge base and must not become a competing CRM or research store.

## Canonical truth
Google Drive is the canonical source of truth for business requirements, source intelligence, Market Research, Lead Engine records, Discovery Command Center, decisions, phase plans, run contracts and active system manifests.

Exact Drive IDs and current manifest/run-contract references must be supplied in the execution handoff. **Do not commit private Drive IDs, lead data, community data, credentials or internal hotel information to this public repository.**

## Current business phase
DISCOVERY.

The business architecture separates three source domains:
- Community Intelligence
- Hotel Intelligence
- Competitor Intelligence

These feed normalized Market Research and the Lead Engine, which feed the Discovery Command Center. Do not collapse these domains into one technical table without an explicit schema handoff.

## Phase gates
- Phase 0: first 100 hotels + market-source expansion + founder operational discovery.
- Phase 1: permitted community expansion + competitor-intelligence pilot.
- Phase 2: CRM automation and dashboard polish.

**Do not start Phase-2 backend/CRM automation merely because it is technically possible.** The task handoff must explicitly state that the current business-layer start gate is satisfied.

## Repository scope
Use this codebase for repeatable technical work such as:
- ingest/normalization;
- hotel and person entity resolution;
- enrichment;
- scoring and prioritization;
- QA and run manifests;
- approved public-source collection pipelines;
- export/sync adapters for the canonical structured store;
- later CRM sync/backend/dashboard infrastructure after the phase gate;
- outreach **draft generation**, never automatic sending unless a later explicit human-approved system contract permits it.

## Non-negotiable rules
- Raw inputs are immutable.
- Unknown values remain unknown; never fabricate enrichment.
- Distinguish `NOT_OBSERVED` from verified absence when modeling competitor/hotel capabilities.
- Every consequential enriched field should retain source/provenance where practical.
- Do not scrape sources whose terms prohibit automated collection or where authorization is unclear.
- Do not store sensitive personal data, guest PII, credentials or private hotel secrets.
- Do not send cold email, DMs or other outbound communication from code without an explicit human gate.
- A contact is not a qualified lead by itself. Qualification requires context/evidence, a problem or conversation reason, and a next-action hypothesis.
- Keep code/config changes minimal and testable.

## Data contract alignment
Technical outputs must map cleanly to canonical concepts supplied in the handoff, including where relevant:
- Hotel
- Person
- Opportunity
- Outreach Queue
- Contact History
- Enrichment Queue
- Competitor Set / Observation / Benchmark / Opportunity Gap
- source/provenance identifiers

Market patterns and service hypotheses remain business-layer objects and should not be redefined in code without an explicit schema change handoff.

## CRM direction
During core Discovery, Google Drive/Sheets remains the business source of truth. The planned future sales CRM is HubSpot for **curated qualified** companies/contacts/deals/activity, not raw research. ClickUp may become an optional operations layer. Never create a competing canonical store from this repository.

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
- current phase and task-specific run contract;
- input source;
- allowed/forbidden actions;
- output schema;
- completion criteria;
- write-back destination.

If those are missing and materially affect correctness, inspect the current project handoff/context before changing code rather than inventing architecture.
