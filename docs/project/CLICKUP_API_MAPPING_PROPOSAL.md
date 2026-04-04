# ClickUp API Mapping Proposal

## Stav

Toto je návrh mapping vrstvy bez ostrej API integrácie.

## Config

- [configs/clickup_api_mapping.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_api_mapping.yaml)

## Preview artifact

- [data/qa/clickup_api_mapping_preview.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_api_mapping_preview.json)

## Cieľ

Oddeliť field mapping od runtime logiky a pripraviť budúci ClickUp API handoff.

## Navrhnuté mapovanie

- `Task name` -> `name`
- `Description content` -> `description`
- `Status` -> `status`
- `Priority` -> `priority`
- ostatné pomocné polia -> `custom.*`

## Neoverené

- presné custom field IDs v cieľovom ClickUp workspace
- finálny API payload contract pre produkciu
