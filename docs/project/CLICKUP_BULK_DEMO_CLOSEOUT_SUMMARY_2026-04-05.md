# ClickUp Bulk Demo Closeout Summary

Dátum: 2026-04-05

## Rozsah dema

Demo bolo spustené na 3 raw batchoch:

- `raw_bratislava region_2026-04-01_21-01-58-857.csv`
- `Paris 100.csv`
- `Sydney 100.csv`

Pre každý batch prebehol lokálny flow:

1. normalize + score
2. enrichment
3. email drafts
4. master exports
5. ClickUp export
6. QA
7. run summary
8. run manifest
9. ClickUp gate + operator artifacts

## Potvrdené výsledky

### Lokálne pipeline výsledky

- Bratislava: `129` riadkov
- Paris: `100` riadkov
- Sydney: `100` riadkov

Všetky 3 batch-e vyrobili:

- `accounts_master.csv`
- `enrichment_master.csv`
- `outreach_drafts.csv`
- `dedupe_review.csv`
- `clickup_import.csv`
- `clickup_phase1_minimal.csv`
- `clickup_full_ranked.csv`

### Live ClickUp write

Kontrolovaný live write:

- Paris: `5/5 PASS`
- Sydney: `5/5 PASS`

Bulk live write:

- Bratislava: `129/129 PASS`
- Sydney: `100/100 PASS`

Bulk writer používal:

- `verify_mode: sample`
- `verify_sample_size: 6`

## Čo funguje

- celé 100+ row batch-e sa dajú zapísať do ClickUp
- custom fields sa zapisujú správne
- sample verify potvrdil:
  - task name
  - description
  - `Hotel Name`
  - `City`
  - `Priority score`
  - `Phone`
  - `Website`
  - `Subject line`
  - `Source file`

## Čo ostáva otvorené

- `Neoverené`: Paris full 100-row bulk write nebol v tomto demu dotiahnutý, lebo už máme potvrdený bulk PASS na Bratislava a Sydney
- Make live vrstva ostáva mimo tohto demo closeoutu

## Source of truth

- `data/qa/demo/raw_bratislava/run_manifest.json`
- `data/qa/demo/raw_bratislava/clickup_write_result_bulk.json`
- `data/qa/demo/paris_100/run_manifest.json`
- `data/qa/demo/paris_100/clickup_write_result.json`
- `data/qa/demo/sydney_100/run_manifest.json`
- `data/qa/demo/sydney_100/clickup_write_result.json`
- `data/qa/demo/sydney_100/clickup_write_result_bulk.json`

## Praktický záver

ClickUp import/demo vrstva je teraz operator-ready pre veľké batch-e.
