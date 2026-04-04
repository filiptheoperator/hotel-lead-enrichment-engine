# Make Input Validation Checklist

## Cieľ

Pred každým Make handoff overiť, že Make dostáva len platné lokálne artifacty a nemusí dopočítavať business logiku.

## Required inputs

- [data/qa/run_manifest.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_manifest.json)
- [data/qa/clickup_import_gate.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.json)
- [outputs/clickup/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/outputs/clickup/raw_bratislava%20region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv)
- [data/qa/clickup_import_dry_run_sample.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_dry_run_sample.csv)
- [data/qa/high_leads_preimport_checklist.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/high_leads_preimport_checklist.csv)
- [data/qa/operator_decision_summary.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/operator_decision_summary.txt)

## Validation kroky

1. required artifact existuje
2. artifact path sedí s `run_manifest.json`
3. `decision` v gate je explicitne prítomné
4. pri `decision = NO_GO` sa Make končí bez live write pokusu
5. Make nečíta `manual_review_shortlist.csv` ako import source
6. paths ostávajú relatívne voči repo root
7. žiadny missing artifact sa nesmie ticho ignorovať

## Hard stop

- missing required artifact
- broken path v payloade
- chýbajúce `decision`
- pokus o live execution pri `NO_GO`
