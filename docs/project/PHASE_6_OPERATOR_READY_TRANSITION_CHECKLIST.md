# Phase 6 Operator Ready Transition Checklist

## Cieľ

Potvrdiť, že batch sa môže posunúť z `READY_FOR_PLANNING` do `READY_FOR_LIVE_CUTOVER`.

## Checklist

1. gate decision je `GO`
2. payload validation je bez issues
3. archive cross-check je plne `ok`
4. ClickUp rehearsal je `PASS`
5. partial write nie je otvorený
6. external blocker nie je otvorený
7. operator handoff bundle je vyplnený
8. pre-launch checklist JSON aj TXT existujú
9. execution day SOP je otvorený a známy
10. rollback owner je potvrdený

## Výsledok

- všetko `yes` -> `READY_FOR_LIVE_CUTOVER`
- aspoň jedno interné `no` -> `READY_FOR_REMEDIATION`
- external blocker -> `BLOCKED_EXTERNAL`
