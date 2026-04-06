# Target Architecture

## High-level flow
```text
Apify raw export
→ raw loader
→ cleaner / normalizer
→ ranked accounts
→ enrichment engine
→ hotel markdown briefs
→ email draft engine
→ CRM export layer
→ manual QA
→ outreach readiness
```

## Core modules
1. ingest
2. normalize
3. score
4. enrich
5. compose
6. export
7. qa
8. orchestrate

## Required outputs
- raw copy archive
- normalized dataset
- ranked dataset
- enrichment master dataset
- per-hotel markdown files
- email drafts dataset
- ClickUp import datasets
- QA logs

## Design rule
Workflow musí byť:
- opakovateľný,
- čitateľný,
- logický,
- modulárny,
- ľahko opraviteľný.

## Orchestration rule
Make.com je glue vrstva.
Mozog workflowu má byť v kóde a configoch.
