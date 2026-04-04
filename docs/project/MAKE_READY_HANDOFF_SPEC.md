# Make-Ready Handoff Spec

## Cieľ

Pripraviť presný handoff pre budúcu Make vrstvu bez presunu business logiky mimo Python pipeline.

## Trigger

- manuálny batch run
- neskôr plánovaný trigger nad lokálnym Python runnerom

## Vstupy

- [data/qa/run_manifest.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_manifest.json)
- [data/qa/clickup_import_gate.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.json)
- [data/qa/clickup_import_dry_run_sample.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_dry_run_sample.csv)
- [outputs/clickup/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/outputs/clickup/raw_bratislava%20region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv)

## Stop conditions

- `fetch_incident_flag = yes`
- `qa_blocking_rows > 0`
- `decision = NO_GO` v `clickup_import_gate.json`
- chýba ClickUp CSV

## Output pre Make

- notifikácia operátorovi
- odovzdanie cesty na ClickUp CSV iba pri `GO`
- odovzdanie cesty na dry run sample
- odovzdanie cesty na archive folder

## Notification text template

### GO

`Batch pripravený na ClickUp import. Skontroluj dry run sample a pokračuj importom.`

### NO-GO

`Batch nie je pripravený na ClickUp import. Skontroluj clickup_import_gate.txt a QA artifacty.`

## Čo Make nemá robiť

- enrichment parsing
- scoring logiku
- QA rozhodovanie
- shortlist triage logiku
