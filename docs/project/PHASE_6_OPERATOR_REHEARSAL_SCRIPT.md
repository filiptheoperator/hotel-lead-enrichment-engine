# Phase 6 Operator Rehearsal Script

## Cieľ

Prejsť execution deň nanečisto bez domýšľania a potvrdiť, že operator vie stopnúť run v každom rizikovom bode.

## Rehearsal mód

- rehearsal_type: `DESK_CHECK`
- make_unblock_required: `no`
- output: `operator readiness verdict`

## Script

1. otvor [PHASE_6_CONTROLLED_LIVE_MAKE_RUN_PLAN.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_CONTROLLED_LIVE_MAKE_RUN_PLAN.md)
2. otvor [PHASE_6_LIVE_CUTOVER_GATE_DECISION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_LIVE_CUTOVER_GATE_DECISION_CHECKLIST.md)
3. otvor [PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_MAKE_TO_CLICKUP_EXECUTION_EVIDENCE_TEMPLATE.md)
4. otvor [PHASE_6_FINAL_GO_LIVE_ROLLBACK_BOUNDARIES.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_FINAL_GO_LIVE_ROLLBACK_BOUNDARIES.md)
5. nahlas potvrď aktuálny Phase 6 stav
6. nahlas pomenuj external blocker a stop podmienku
7. ukáž presné poradie `teams -> interface -> logs -> run`
8. ukáž, kde sa zapisuje execution evidence
9. vysvetli, kedy sa run označí ako `BLOCKED`
10. vysvetli, kedy sa run označí ako `FAIL`
11. vysvetli, kedy je dovolené dať `GO`
12. ukáž rollback boundaries a safe-stop pravidlá

## Kontrolné otázky

- čo sa stane, ak `teams` nevráti čitateľný výsledok?
- čo sa stane, ak `interface` prejde, ale `logs` nie?
- čo sa stane, ak po `run` nesedí task count?
- čo sa stane, ak vznikne partial write?
- kde sa zapisuje blocker reference?

## Rehearsal PASS

- operator nepotrebuje dopĺňať kroky z hlavy
- vie pomenovať hard stop body
- vie ukázať required template-y a checklisty
- vie klasifikovať `PASS | BLOCKED | FAIL`

## Rehearsal FAIL

- operator preskočí gate krok
- operator nevie určiť, čo je prvý write krok
- operator nevie ukázať evidence alebo rollback postup
- operator nevie odpovedať na kontrolné otázky

## Simulated výsledok

- rehearsal_status: `PASS_DESK_CHECK`
- gap_found: `none_blocking`
- note: `workflow je čitateľný aj bez Make unblocking; ostrý run ostáva blokovaný len na EXT-MAKE-001`
