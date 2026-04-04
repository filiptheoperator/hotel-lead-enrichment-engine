# CODEX PROJECT BRIEF

## Project name
Hotel Lead Enrichment Engine OS

## Core goal
Build a stable Python workflow for independent 3–4 star hotel lead enrichment.

## Workflow target
raw ingest → normalize → score → enrich → email drafts → ClickUp export → QA → run summary

## Working language
When guiding the user, communicate in Slovak.

## Build rules
- Keep architecture simple.
- Do not add unnecessary tools.
- Do not introduce enterprise complexity.
- Build in phases only.
- Do not skip phases.
- Prefer local Python-first workflow.
- Make is only a glue layer later.
- Keep configs separate from code.
- Keep prompts separate from code.
- Do not overwrite raw input files.
- Mark unverified data clearly.

## Priorities
1. pipeline stability
2. data quality
3. enrichment quality
4. email relevance
5. CRM cleanliness
6. only then further automation

## Current phase
Fáza 3:
operator-ready workflow

## Target stack
- Python
- VS Code
- Codex
- Apify
- ClickUp
- Make
- GitHub

## Enrichment rule
If publicly available, include opening hours.
If something is unverified, label it clearly.
