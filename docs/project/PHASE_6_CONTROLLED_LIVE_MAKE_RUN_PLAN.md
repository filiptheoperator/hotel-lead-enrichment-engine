# Phase 6 Controlled Live Make Run Plan

## Cieľ

Spustiť minimálny live Make sled až po odblokovaní siete a len v kontrolovanom poradí bez improvizácie.

## Operator verzia

- document_status: `FINAL_OPERATOR_VERSION`
- execution_mode: `MINIMAL_RETEST_THEN_SINGLE_CONTROLLED_RUN`
- scope_freeze: `ACTIVE`

## Predpoklady

- Phase 6 stav je `READY_PENDING_EXTERNAL_UNBLOCK`
- ClickUp live path je `PASS`
- `EXT-MAKE-001` je vyriešený alebo explicitne uvoľnený na retest
- payload contract ostáva `LOCKED`

## Required vstupy pred štartom

- [PHASE_6_LIVE_CUTOVER_GATE_DECISION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_CUTOVER_GATE_DECISION_CHECKLIST.md) je vyplnený
- [PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md) je pripravený
- [PHASE_6_LIVE_OUTPUT_VERIFICATION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_OUTPUT_VERIFICATION_CHECKLIST.md) je otvorený
- rollback owner je známy
- operator vie, kde je finálny payload a gate súbor

## Presné poradie

1. potvrdiť `GO` alebo `BLOCKED` v gate checklistu
2. potvrdiť, že `HTTP 403 / Cloudflare 1010` už neplatí
3. zapísať štart execution do evidence template
4. spustiť `python3 src/make_id_helper.py --mode teams`
5. ak `teams` nie je čitateľný, okamžite označiť run `BLOCKED` alebo `FAIL`
6. spustiť `python3 src/make_scenario_test_run.py --mode interface`
7. ak `interface` nie je čitateľný, nepokračovať na write krok
8. spustiť `python3 src/make_scenario_test_run.py --mode logs`
9. ak `logs` nie je čitateľný, nepokračovať na write krok
10. až potom spustiť `python3 src/make_scenario_test_run.py --mode run --input-json data/qa/make_input_pack_go.json`
11. uložiť run výsledok a doplniť execution evidence
12. spraviť output verification podľa checklistu
13. potvrdiť ClickUp výsledok proti required fieldom a task countu
14. uzavrieť run ako `PASS`, `BLOCKED` alebo `FAIL`

## Rozhodovacie pravidlá

- `BLOCKED`: sieť alebo externý prístup stále bráni čitateľnému Make výsledku
- `FAIL`: run prebehol, ale output alebo ClickUp verifikácia nesedí
- `PASS`: všetky tri pre-check kroky sú čitateľné, run output sedí a ClickUp verification je čistá

## Zakázané skratky

- preskočiť `teams`, `interface` alebo `logs`
- spustiť `run` pri `NO_GO`
- meniť payload scope počas execution dňa
- opakovať run naslepo bez review predošlého výstupu

## Hard stop

- vracia sa `403`
- objaví sa `Cloudflare 1010`
- interface alebo logs krok nevráti čitateľný výsledok
- operator nevie potvrdiť, aký payload bol použitý
- chýba gate decision alebo evidence template

## Výstupy po ukončení

- vyplnený execution evidence template
- výsledok `PASS | BLOCKED | FAIL`
- vyplnený output verification checklist
- ak treba, vyplnený failure triage sheet

## Naviazané dokumenty

- [MAKE_RESUME_POINT_NOTE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_RESUME_POINT_NOTE.md)
- [MAKE_LAUNCH_CHECKLIST_MINIMAL.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_LAUNCH_CHECKLIST_MINIMAL.md)
- [PHASE_6_LIVE_OUTPUT_VERIFICATION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_OUTPUT_VERIFICATION_CHECKLIST.md)
- [PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md)
- [PHASE_6_LIVE_FAILURE_TRIAGE_SHEET.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_FAILURE_TRIAGE_SHEET.md)
