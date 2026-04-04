# ClickUp / Make Integration Brief

## Stav

Toto je integračný brief pre budúcu fázu.
Nejde o implementáciu.

## Cieľ

Napájať iba stabilné lokálne artifacty.
Make nemá niesť business logiku enrichmentu ani QA.

## Vstupy pre budúcu integráciu

- [outputs/clickup/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/outputs/clickup/raw_bratislava%20region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv)
- [data/qa/run_manifest.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_manifest.json)
- [data/qa/run_summary.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_summary.txt)
- [data/qa/manual_review_shortlist.csv](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/manual_review_shortlist.csv)

## Odporúčaný contract pre ClickUp fázu

- importovať iba riadky z ClickUp CSV
- pred importom čítať `run_manifest.json`
- zablokovať import pri:
  - `fetch_incident_flag = yes`
  - `qa_blocking_rows > 0`
- `manual_review_shortlist.csv` nepoužiť ako import source
- shortlist použiť iba ako review queue

## Odporúčaný contract pre Make fázu

- Make má robiť:
  - trigger runu
  - archiváciu artifactov
  - notifikáciu operátorovi
  - podmienené odovzdanie ClickUp CSV
- Make nemá robiť:
  - parsing hotelových webov
  - enrichment heuristiky
  - QA scoring
  - shortlist rozhodovanie

## Potrebné mapovania pre budúcu integráciu

- `Task name` -> názov tasku
- `Description content` -> telo tasku
- `Status` -> importný status
- `Priority` -> ClickUp numeric priority
- `Hotel name`, `City`, `Priority score`, `Contact phone`, `Contact website`, `Subject line`, `Source file` -> pomocné polia

## Otvorené neoverené body

- presné ClickUp field mapping v cieľovom workspace
- či import pôjde cez CSV import alebo API
- presný Make trigger model
- retry správanie pri externých zlyhaniach
