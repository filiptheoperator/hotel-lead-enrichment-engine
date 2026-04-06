# Make Unblock Run Packet

## Cieľ

Jedno rozcestie pre execution deň po odblokovaní Make siete.

## Otvor v tomto poradí

1. [PHASE_6_READINESS_SUMMARY.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_READINESS_SUMMARY.md)
2. [PHASE_6_OPERATOR_READY_TRANSITION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_OPERATOR_READY_TRANSITION_CHECKLIST.md)
3. [PHASE_6_EXECUTION_DAY_SOP.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_EXECUTION_DAY_SOP.md)
4. [PHASE_6_CONTROLLED_LIVE_MAKE_RUN_PLAN.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_CONTROLLED_LIVE_MAKE_RUN_PLAN.md)
5. [PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md)
6. [PHASE_6_LIVE_OUTPUT_VERIFICATION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_OUTPUT_VERIFICATION_CHECKLIST.md)
7. [PHASE_6_LIVE_FAILURE_TRIAGE_SHEET.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_FAILURE_TRIAGE_SHEET.md)
8. [PHASE_6_LIVE_RETEST_CLOSEOUT_TEMPLATE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_RETEST_CLOSEOUT_TEMPLATE.md)

## Runtime príkazy

1. `python3 src/make_id_helper.py --mode teams`
2. `python3 src/make_scenario_test_run.py --mode interface`
3. `python3 src/make_scenario_test_run.py --mode logs`
4. `python3 src/make_scenario_test_run.py --mode run --input-json data/qa/make_input_pack_go.json`

## Incident SOP odkazy

- [HTTP_5XX_RETRY_SOP.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/HTTP_5XX_RETRY_SOP.md)
- [HTTP_4XX_REQUEST_FIX_SOP.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/HTTP_4XX_REQUEST_FIX_SOP.md)
- [NETWORK_ERROR_RETRY_SOP.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/NETWORK_ERROR_RETRY_SOP.md)
- [CLOUDFLARE_1010_UNBLOCK_ESCALATION_SOP.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLOUDFLARE_1010_UNBLOCK_ESCALATION_SOP.md)
- [PHASE_6_FINAL_GO_LIVE_ROLLBACK_BOUNDARIES.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_FINAL_GO_LIVE_ROLLBACK_BOUNDARIES.md)

## Čo nerobiť

- nepreskočiť `teams -> interface -> logs`
- nespúšťať retry naslepo pri `HTTP 4xx`
- neopakovať blokovaný run pri `Cloudflare 1010` z tej istej siete
- nemeniť payload scope počas execution dňa
