# External Blocker Register

## Blocker 1

- id: `EXT-CLICKUP-001`
- system: `ClickUp`
- title: `Custom field usage plan limit`
- code: `FIELD_033`
- status: `RESOLVED`
- impact: `historický blocker, už neblokuje Phase 5`
- workaround: `n/a`
- evidence: [data/qa/clickup_rehearsal_execution.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_rehearsal_execution.json)

## Blocker 2

- id: `EXT-CLICKUP-002`
- system: `ClickUp`
- title: `Partial write cleanup decision`
- code: `N/A`
- status: `RESOLVED`
- impact: `historický rehearsal detail, live PASS je potvrdený`
- workaround: `n/a`
- evidence: [docs/project/CLICKUP_PARTIAL_WRITE_CLEANUP_SOP.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLICKUP_PARTIAL_WRITE_CLEANUP_SOP.md)

## Blocker 3

- id: `EXT-MAKE-001`
- system: `Make`
- title: `Cloudflare access deny before Make API processing`
- code: `HTTP 403 / Cloudflare 1010`
- status: `OPEN`
- impact: `blokuje Make API teams, interface aj ping test; Make debugging je pozastavený`
- workaround: `zmeniť sieť alebo stroj a zopakovať len minimálny retest sled`
- evidence: [data/qa/make_scenario_test_result.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/make_scenario_test_result.json)
