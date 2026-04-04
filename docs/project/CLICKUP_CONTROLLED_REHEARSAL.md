# ClickUp Controlled Rehearsal

## Cieľ

Prvý kontrolovaný rehearsal na malej vzorke bez ostrého batch importu.

## Primárne artifacty

- [data/qa/clickup_import_dry_run_sample.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_dry_run_sample.csv)
- [data/qa/clickup_import_dry_run_sample_high_only.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_dry_run_sample_high_only.csv)
- [data/qa/high_leads_preimport_checklist.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/high_leads_preimport_checklist.csv)
- [data/qa/clickup_import_gate.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.txt)

## Rehearsal scope

- sample size: `5`
- zdroj: latest ClickUp import CSV
- účel: overiť field mapping, nie ostrý import celého batchu

## Rehearsal kroky

1. skontrolovať `clickup_import_gate.txt`
2. ak je `NO_GO`, rehearsal je len formálny review sample, nie import
3. otvoriť `clickup_import_dry_run_sample.csv`
4. skontrolovať field-by-field:
   - `Task name`
   - `Description content`
   - `Status`
   - `Priority`
   - `Hotel name`
   - `City`
   - `Contact phone`
   - `Contact website`
   - `Subject line`
5. porovnať `High` leady s `high_leads_preimport_checklist.csv`

## Neoverené

- reálne správanie ClickUp workspace
- či rehearsal prebehne cez CSV importer alebo API sandbox
