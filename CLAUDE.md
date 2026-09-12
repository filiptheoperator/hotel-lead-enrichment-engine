# HOTEL AI DISCOVERY — CLAUDE CODE INSTRUCTIONS

You are working inside the technical Lead Engine / future automation layer for The Hotel Operator / Hotel AI.

## Current phase: DISCOVERY
Do not optimize for scale before evidence quality. The system exists to discover hotel-market problems, enrich relevant hotels/people, benchmark competitors, support high-quality conversations, and return real discovery learnings to the canonical business knowledge base.

## Canonical architecture
Business truth is external to this repository in Google Drive. The active Drive bootstrap/manifest, current phase plan, task-specific RUN contract and exact IDs must be provided through the task handoff. This public repo must not contain private Drive IDs, CRM records, raw community member data, credentials, guest PII or confidential hotel information.

Three source domains are intentionally separate:
- Community Intelligence
- Hotel Intelligence
- Competitor Intelligence

They feed Market Research + Lead Engine, which feed the Discovery Command Center. Do not merge domain ownership or redefine source-of-truth semantics in code without explicit business-layer approval.

## Phase gates
- Phase 0: first 100 hotels, market research source expansion, founder operational discovery.
- Phase 1: permitted communities and one competitor-intelligence pilot.
- Phase 2: CRM automation / dashboard polish.

Do not implement Phase-2 CRM/backend work until the handoff explicitly confirms the business start gate is met.

## Your responsibilities
Prefer small, robust code changes for:
- normalization and entity resolution;
- enrichment with explicit provenance;
- hotel/person/opportunity scoring;
- competitor observation/benchmark normalization when requested;
- QA;
- repeatable exports/imports;
- later database/API/dashboard/CRM synchronization when the current RUN contract explicitly requests it.

## Guardrails
- Never fabricate missing data.
- Preserve raw inputs.
- `NOT_OBSERVED` is not verified absence.
- Never silently change scoring/business semantics.
- Do not automatically send email/DM/outreach.
- Do not implement scraping against sources that prohibit automation or where permission is unresolved.
- Keep personal data minimized to professionally relevant, permitted information.
- Never turn a hypothesis into a verified fact.

## Expected business objects
Hotel / Person / Opportunity / Outreach Queue / Contact History / Enrichment Queue, plus source/provenance keys. Competitor workflows may additionally include Competitor Set / Observation / Benchmark / Opportunity Gap.

A useful opportunity explains: who/which hotel, what problem or evidence, why now, possible value, confidence, and next action.

## CRM direction
Google Drive/Sheets remains the canonical business source of truth during Discovery. HubSpot is the preferred future sales CRM only for curated qualified companies, professional contacts, deals and activity once Phase 2 is authorized. Raw research does not move into HubSpot. ClickUp is optional for operations, not canonical evidence.

## Working style
Read repository docs/configs first. Reuse existing pipeline components before introducing frameworks. Add tests or QA checks for consequential changes. Require a handoff with current phase + task-specific RUN contract before substantial changes. Treat any task that changes canonical schemas as blocked until the business-layer data contract is explicitly updated or supplied in the handoff.
