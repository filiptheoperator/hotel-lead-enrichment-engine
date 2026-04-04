# ClickUp Rehearsal Operator Checklist

## Použitie

Tento checklist je určený pre prvý controlled rehearsal v reálnom ClickUp workspace.
Aktuálny batch gate je [data/qa/clickup_import_gate.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.json) = `NO_GO`, takže rehearsal je dovolený len ako izolovaný test v test workspace.

## Pred štartom

- potvrď, že write target je test list alebo test folder
- nepotvrdzuj batch cutover
- otvor [docs/project/CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md)
- otvor [docs/project/CLICKUP_CUSTOM_FIELD_IDS_AND_MAPPING.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLICKUP_CUSTOM_FIELD_IDS_AND_MAPPING.md)
- otvor [data/qa/clickup_import_dry_run_sample.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_dry_run_sample.csv)

## Workspace kontrola

- potvrď názov workspace
- potvrď názov test listu alebo test foldera
- potvrď, že required custom fields existujú
- skopíruj live field IDs pre:
- `Hotel name`
- `City`
- `Priority score`
- `Subject line`
- `Source file`

## Sample výber

- vyber `3 až 5` riadkov z dry run sample
- preferuj `High` leady
- nezapisuj celý batch

## Write kontrola

Pre každý vytvorený task skontroluj:

- `name`
- `description`
- `status`
- `priority`
- `Hotel name`
- `City`
- `Priority score`
- `Subject line`
- `Source file`
- `Contact phone`, ak field existuje
- `Contact website`, ak field existuje

## Pass podmienky

- required fields sú zapísané bez manuálneho zásahu
- žiadne required pole neskončí v nesprávnom fielde
- `description` nie je zrezaný alebo poškodený
- logické mapovanie sedí s configom

## Fail podmienky

- chýba required field ID
- field type nesedí
- hodnota skončí v nesprávnom fielde
- write zlyhá na valid sample riadku

## Po rehearsal

- vyplň [docs/project/CLICKUP_REHEARSAL_RESULT_TEMPLATE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLICKUP_REHEARSAL_RESULT_TEMPLATE.md)
- ak výsledok nie je `PASS`, neurob live cutover
- ak sa mení mapping alebo field ID, oprav najprv config
