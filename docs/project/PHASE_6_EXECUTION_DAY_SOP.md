# Phase 6 Execution Day SOP

## Cieľ

Dať operátorovi finálny presný sled krokov pre deň, keď sa Make sieť odblokuje.

## Pred štartom

1. otvor [PHASE_6_READINESS_SUMMARY.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_READINESS_SUMMARY.md)
2. otvor [PHASE_6_LIVE_CUTOVER_GATE_DECISION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_CUTOVER_GATE_DECISION_CHECKLIST.md)
3. otvor [PHASE_6_CONTROLLED_LIVE_MAKE_RUN_PLAN.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_CONTROLLED_LIVE_MAKE_RUN_PLAN.md)
4. otvor [PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md)
5. potvrď, že `EXT-MAKE-001` už neblokuje sieť

## Execution sled

1. vyplň gate decision
2. spusti `python3 src/make_id_helper.py --mode teams`
3. spusti `python3 src/make_scenario_test_run.py --mode interface`
4. spusti `python3 src/make_scenario_test_run.py --mode logs`
5. ak sú tri pre-check kroky čitateľné, spusti `python3 src/make_scenario_test_run.py --mode run --input-json data/qa/make_input_pack_go.json`
6. ulož result a doplň execution evidence
7. sprav output verification
8. sprav ClickUp verification
9. uzavri výsledok ako `PASS | BLOCKED | FAIL`
10. vyplň post-live review

## Hard stop

- `HTTP 403`
- `Cloudflare 1010`
- nečitateľný `teams`, `interface` alebo `logs` výsledok
- task count mismatch
- required field mismatch
- partial write bez uzavretej evidencie

## Po rune

- [PHASE_6_LIVE_OUTPUT_VERIFICATION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_OUTPUT_VERIFICATION_CHECKLIST.md)
- [PHASE_6_LIVE_FAILURE_TRIAGE_SHEET.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_FAILURE_TRIAGE_SHEET.md)
- [PHASE_6_POST_LIVE_REVIEW_TEMPLATE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_POST_LIVE_REVIEW_TEMPLATE.md)
