# HOTEL AI DISCOVERY — CLAUDE CODE INSTRUCTIONS

You are working inside the technical Lead Engine for The Hotel Operator / Hotel AI.

## Current phase: DISCOVERY
Do not optimize for scale before evidence quality. The system exists to discover hotel-market problems, enrich relevant hotels/people, support high-quality conversations, and return real discovery learnings to the canonical business knowledge base.

## Canonical architecture
Business truth is external to this repository in Google Drive. The active Drive bootstrap/manifest and exact IDs must be provided through the task handoff. This public repo must not contain private Drive IDs, CRM records, raw community member data, credentials, guest PII or confidential hotel information.

## Your responsibilities
Prefer small, robust code changes for:
- normalization and entity resolution;
- enrichment with explicit provenance;
- hotel/person/opportunity scoring;
- QA;
- repeatable exports/imports;
- later database/API/dashboard infrastructure when the current manifest explicitly requests it.

## Guardrails
- Never fabricate missing data.
- Preserve raw inputs.
- Never silently change scoring/business semantics.
- Do not automatically send email/DM/outreach.
- Do not implement scraping against sources that prohibit automation or where permission is unresolved.
- Keep personal data minimized to professionally relevant, permitted information.
- Never turn a hypothesis into a verified fact.

## Expected lead objects
Hotel → Person → Opportunity → Outreach Queue → Contact History.

A useful opportunity explains: who, what problem/evidence, why now, possible value, confidence, and next action.

## Working style
Read repository docs/configs first. Reuse existing pipeline components before introducing frameworks. Add tests or QA checks for consequential changes. Treat any task that changes canonical schemas as blocked until the business-layer data contract is explicitly updated or supplied in the handoff.
