# HOTEL AI DISCOVERY — CLAUDE CODE INSTRUCTIONS

## Business identity

**The Hotel Operator** — https://thehoteloperator.com/

This repository is the canonical technical backend codebase for HOTEL AI DISCOVERY. Read `AGENTS.md`, `docs/BUSINESS_CONTEXT.md`, `docs/BACKEND_ROADMAP.md` and the task-specific runtime handoff before repo-scale work.

## Current phase: DISCOVERY
Do not optimize for scale before evidence quality. The system exists to discover hotel-market problems, enrich relevant hotels/people, benchmark competitors, support high-quality conversations, and return real discovery learnings to the canonical business knowledge base.

The public website is a positioning/acquisition surface, not proof that any service hypothesis is validated.

## Canonical architecture
Business truth is external to this repository in Google Drive. The active Drive bootstrap/manifest, current phase plan, task-specific RUN/TECH_RUN contract and exact IDs must be provided through the task handoff. This public repo must not contain private Drive IDs, CRM records, raw community member data, credentials, guest PII or confidential hotel information.

Three source domains are intentionally separate:
- Community Intelligence
- Hotel Intelligence
- Competitor Intelligence

They feed Market Research + Lead Engine, which feed the Discovery Command Center. Do not merge domain ownership or redefine source-of-truth semantics in code without explicit business-layer approval.

## Phase gates
- Phase 0: first 100 hotels, market research source expansion, founder operational discovery.
- Phase 1: permitted communities and one competitor-intelligence pilot.
- Phase 2: CRM automation / dashboard polish.

Technical foundation work may proceed during Phase 0 when explicitly covered by the active TECH_RUN. Do not implement Phase-2 CRM/backend automation simply because it is technically feasible.

## Your responsibilities
Prefer small, robust, testable changes for:
- exact-ID Drive read/mirror foundations;
- versioned schemas/contracts;
- normalization and entity resolution;
- enrichment with explicit provenance;
- hotel/person/opportunity scoring;
- competitor observation/benchmark normalization;
- run state/audit/QA;
- dry-run diffs and controlled write-back;
- repeatable exports/imports;
- later database/API/dashboard/CRM synchronization when the current RUN contract explicitly requests it.

## Where Claude Code adds the most value
Use Claude Code especially for:
- broad repository comprehension across many files;
- architecture challenge before large refactors;
- multi-file refactors after plan approval;
- cross-contract/schema consistency checks;
- security/permission-boundary analysis;
- idempotency and failure-mode review;
- entity-resolution edge cases;
- independent review of a Codex implementation;
- test-suite design and gap analysis;
- subagent decomposition when independent technical modules can be reviewed separately.

Start large or risky work in Plan mode. Findings should be classified as `ACCEPT`, `FIX`, `DEFER`, or `OPTIONAL` with evidence.

## Google Drive posture
Claude Code may use Google Drive only through an explicitly configured, permission-scoped MCP/connector or approved local integration.

Default posture:
- READ canonical requirements/contracts by exact ID where available;
- local mirrors are temporary technical snapshots, never authoritative;
- fail closed on manifest/schema mismatch;
- do not log credentials/private data.

WRITE posture:
- generic Drive mutation is forbidden;
- any Sheets writer must be exact-ID allowlisted, schema-checked, dry-run capable, idempotent and audited;
- write access must be explicitly authorized by the current task/run;
- Claude Code must never decide on its own that local repo state overrides canonical Drive business truth.

## Guardrails
- Never fabricate missing data.
- Preserve raw inputs.
- `NOT_OBSERVED` is not verified absence.
- Never silently change scoring/business semantics.
- Do not automatically send email/DM/outreach.
- Do not implement scraping against sources that prohibit automation or where permission is unresolved.
- Keep personal data minimized to professionally relevant, permitted information.
- Never turn a hypothesis into a verified fact.
- Never commit private Drive IDs, raw research datasets, community/lead records, credentials or confidential hotel data to this public repo.

## Expected business objects
Community Source / Thread / Contribution / Community Signal; Hotel / Person / Tech Stack; Opportunity / Outreach Queue / Contact History / Enrichment Queue; Competitor Set / Observation / Benchmark / Opportunity Gap; Market Signal; Run State / Audit Event.

A useful opportunity explains: who/which hotel, what problem or evidence, why now, possible value, confidence, and next action.

## CRM direction
Google Drive/Sheets remains the canonical business source of truth during Discovery. HubSpot is the preferred future sales CRM only for curated qualified companies, professional contacts, deals and activity once Phase 2 is authorized. Raw research does not move into HubSpot. ClickUp is a legacy/optional adapter, not canonical evidence.

## Working style
Read repository docs/configs first. Reuse existing pipeline components before introducing frameworks. Add tests for consequential changes. Require a handoff with current phase + task-specific RUN/TECH_RUN contract before substantial changes. Treat any task that changes canonical schemas as blocked until the business-layer data contract is explicitly updated or supplied in the handoff.

The reusable Claude skill for this project lives at `.claude/skills/hotel-discovery-backend/SKILL.md`.

## Verification
At minimum for substantive changes:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Never weaken safety boundaries merely to obtain a passing run.