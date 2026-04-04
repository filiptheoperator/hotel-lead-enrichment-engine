# Fáza 4 - Kickoff Brief

## Stav

Fáza 4 začína nad potvrdeným stavom `operator-ready workflow` z Fázy 3.

## Východiskový checkpoint

- branch: `main`
- commit: `d9fe47f`
- Phase 3 status: uzavretá

## Cieľ Fázy 4

Pripraviť kontrolovaný prechod z lokálneho Python-first workflow do reálneho ClickUp / Make integračného rehearsal bez presunu business logiky mimo existujúci projekt.

## Scope

1. uzamknúť finálny ClickUp API payload contract
2. potvrdiť finálne custom field IDs a mapping
3. pripraviť a zdokumentovať prvý controlled ClickUp rehearsal v reálnom workspace
4. pripraviť Make execution payload contract
5. definovať error handling a retry pravidlá
6. uzamknúť Phase 4 Definition of Done

## Existujúce vstupy

- [docs/project/PHASE_3_DONE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_3_DONE.md)
- [docs/project/INTEGRATION_READINESS_REPORT.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/INTEGRATION_READINESS_REPORT.md)
- [data/qa/run_manifest.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_manifest.json)
- [data/qa/clickup_import_gate.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.json)
- [data/qa/clickup_api_mapping_preview.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_api_mapping_preview.json)
- [data/qa/clickup_api_mapping_validation.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_api_mapping_validation.json)

## Blokery prenesené z Fázy 3

- živý ClickUp rehearsal je stále `Neoverené`
- finálne custom field IDs sú stále `Neoverené`
- živý API contract proti cieľovému workspace je stále `Neoverené`

## Pravidlá Fázy 4

- zdroj pravdy ostáva lokálna Python pipeline
- configs ostávajú oddelené od kódu
- mapping ostáva oddelený od runtime logiky
- raw input súbory sa neprepisujú
- neoverené externé údaje sa explicitne označujú
- Make nevlastní enrichment, scoring ani QA rozhodovanie

## Očakávaný výsledok

Na konci Fázy 4 má byť pripravený kontrolovaný live cutover bez nejasností v payload shape, field IDs, stop conditions a retry správaní.
