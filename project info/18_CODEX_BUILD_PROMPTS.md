# Codex Build Prompts

## Prompt A — repo skeleton
Create the initial repository skeleton for a project called Hotel Lead Enrichment Engine OS.
Use Python.
Create these folders and starter files exactly as specified in the project docs.
Do not add extra architecture.
Return only the files and minimal notes.

## Prompt B — raw loader
Build a simple Python raw loader that reads CSV files from data/raw and outputs a normalized dataframe preview.
Do not implement enrichment yet.
Keep it beginner-safe and simple.

## Prompt C — normalize and rank
Build a normalization and ranking layer that transforms raw hotel lead CSV data into a ranked accounts CSV.
Use config-driven scoring placeholders.
Keep outputs structured and reproducible.

## Prompt D — enrichment engine v1
Build a first enrichment engine module scaffold.
It should accept ranked hotel inputs and prepare placeholders for:
- commercial profile
- operating hours
- check-in/check-out
- contacts
- clickup-ready fields
- personalization angles
- cold email draft
- follow-up draft
- discovery hypothesis

## Prompt E — export layer
Build an export layer that writes:
- ranked outputs
- enrichment outputs
- per-hotel markdown files
- email draft outputs
- ClickUp import outputs

## Important Codex rule
Aj keď prompt je písaný anglicky kvôli coding clarity, výsledná komunikácia v tomto projekte má zostať po slovensky pri vedení používateľa.
