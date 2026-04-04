# Make Runbook

## Cieľ

Dať operátorovi presný sled krokov pre Make vetvu bez domýšľania.

## Runbook

1. otvor [docs/project/MAKE_INPUT_VALIDATION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_INPUT_VALIDATION_CHECKLIST.md)
2. potvrď required artifacty
3. potvrď `decision` v gate
4. zostav payload podľa [docs/project/MAKE_PAYLOAD_EXAMPLE_PACK.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_PAYLOAD_EXAMPLE_PACK.md)
5. ak `decision = NO_GO`, skonči notifikáciou
6. ak `decision = GO`, odovzdaj payload do Make
7. po behu skontroluj notifikáciu a archive evidence

## Hard stop

- chýba artifact
- gate nie je čitateľný
- payload nie je kompletný
- external blocker nie je správne označený
