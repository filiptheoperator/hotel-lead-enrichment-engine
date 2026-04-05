## Phase 1 Operator Import SOP

1. skontroluj [configs/project.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/project.yaml)
   - `clickup_export_mode: phase1_minimal`
2. spusti pipeline po ClickUp export:
   - `python3 src/normalize_score.py`
   - `python3 src/enrich_hotels.py`
   - `python3 src/email_drafts.py`
   - `python3 src/master_exports.py`
   - `python3 src/clickup_export.py`
   - `python3 src/qa_checks.py`
   - `python3 src/run_report.py`
   - `python3 src/run_manifest.py`
3. otvor [data/qa/run_summary.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_summary.txt)
   - `clickup_export_mode` musí byť `phase1_minimal`
   - `clickup_import_ready_rows` musí byť rovné `clickup_rows`
4. pre operator import použi:
   - [outputs/clickup](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/outputs/clickup)
   - súbor `*_clickup_import.csv`
5. ak chceš bohatší export s `Description content`, použi:
   - `*_clickup_full_ranked.csv`

Poznámka:
- `phase1_minimal` je krátky ClickUp import bez `Description content`
- full notes ostávajú vo `*_clickup_full_ranked.csv`
