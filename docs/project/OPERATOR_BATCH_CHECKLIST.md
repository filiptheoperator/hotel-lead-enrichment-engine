# Operator Batch Checklist

## Cieľ

Krátky operátorský postup po každom batch rune bez potreby čítať celý kód.

## Poradie kontroly

1. Otvor [data/qa/run_manifest.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_manifest.json) a skontroluj:
   - či sedí batch source file
   - či existujú všetky artifact paths
   - či nie je `fetch_incident_flag = yes`
2. Otvor [data/qa/clickup_import_gate.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.txt) a skontroluj:
   - či je batch `GO` alebo `NO_GO`
   - ktoré stop conditions sú aktívne
3. Otvor [data/qa/run_summary.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_summary.txt) a skontroluj:
   - `clickup_import_ready_rows`
   - `qa_blocking_rows`
   - `verified_checkin_checkout`
   - `single_side_checkin_checkout_verified`
4. Otvor [data/qa/run_delta_report.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_delta_report.txt) a skontroluj:
   - či sa náhle nezmenil počet verified / unverified check-in-check-out
   - či shortlist bucket delta nevyskočila kvôli infra incidentu
5. Otvor [data/qa/qa_issues.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/qa_issues.csv) a skontroluj:
   - `global_public_web_fetch_incident`
   - všetky `High` issue
   - ClickUp readiness issue
6. Otvor [data/qa/manual_review_shortlist.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/manual_review_shortlist.csv) a zoradi podľa:
   - `operator_triage_priority`
   - `operator_triage_action`
   - `priority_score`
7. Otvor [data/qa/clickup_import_dry_run_sample.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_dry_run_sample.csv) a skontroluj malú vzorku.
8. Až potom otvor [outputs/clickup/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/outputs/clickup/raw_bratislava%20region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv) a rozhodni o importe.

## Stop podmienky

- `qa_blocking_rows > 0`
- `fetch_incident_flag = yes` pre batch s webovými leadmi
- chýba `run_manifest.json`
- `clickup_import_gate` je `NO_GO`
- chýba ClickUp export artifact

## Go podmienky

- ClickUp export existuje
- `clickup_import_ready_rows` sedí s očakávaným batch countom
- nie je globálny infra incident
- `High` leady majú jasný `operator_triage_action`
