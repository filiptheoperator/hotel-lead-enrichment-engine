# ClickUp Controlled Rehearsal - Live Workspace

## Stav

Tento dokument pripravuje prvý controlled rehearsal v reálnom workspace.
Samotný live rehearsal ešte neprebehol, preto je výsledok stále `Neoverené`.

## Cieľ

Overiť na malej vzorke, že finálny payload contract a custom field mapping fungujú v cieľovom ClickUp workspace bez ostrého batch importu.

## Vstupy

- [data/qa/clickup_import_gate.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.json)
- [data/qa/clickup_import_dry_run_sample.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_dry_run_sample.csv)
- [data/qa/high_leads_preimport_checklist.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/high_leads_preimport_checklist.csv)
- [docs/project/CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md)
- [docs/project/CLICKUP_CUSTOM_FIELD_IDS_AND_MAPPING.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLICKUP_CUSTOM_FIELD_IDS_AND_MAPPING.md)

## Rehearsal scope

- sample size: `3 až 5`
- odporúčaná vzorka: top `High` leady z dry run sample
- write target: dedikovaný test list alebo test folder
- cieľ: validácia mappingu, nie batch throughput

## Gate pred rehearsal

Ak je [data/qa/clickup_import_gate.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.json) v stave `NO_GO`, rehearsal je dovolený iba ako izolovaný test na test workspace a bez batch cutover rozhodnutia.

## Postup

1. potvrdiť test workspace a test list
2. potvrdiť všetky required custom field IDs
3. vybrať 3 až 5 sample riadkov z dry run sample
4. vytvoriť tasky iba z tejto vzorky
5. skontrolovať `name`, `description`, `status`, `priority`
6. skontrolovať všetky required custom fields
7. porovnať uložené hodnoty proti source CSV
8. zdokumentovať pass/fail pre každý field

## Pass criteria

- všetky required fields sa zapíšu bez manuálneho premapovania
- nevznikne truncation alebo zámenné pole
- `name` a `description` ostanú čitateľné
- `Subject line` a `Source file` sa vrátia v správnych custom fieldoch

## Fail criteria

- chýbajúci alebo nesprávny custom field ID
- nesprávny field type
- write zlyhá pre valid sample row
- payload vyžaduje dodatočný transform mimo uzamknutého contractu

## Output z rehearsal

- `rehearsal_status`: `PASS | FAIL | BLOCKED`
- `workspace_confirmed`: `yes | no`
- `validated_field_ids`: zoznam potvrdených IDs
- `field_mismatches`: zoznam mismatchov
- `next_action`: oprava configu alebo povolenie ďalšieho kroku

## Poznámka

Live workspace prístup a výsledok rehearsal sú v tomto repozitári k dnešnému dňu `Neoverené`.
