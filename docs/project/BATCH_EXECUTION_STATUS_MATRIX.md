# Batch Execution Status Matrix

## Statusy

### `READY_FOR_PLANNING`

- planning artefakty môžu pokračovať
- live cutover ešte nie

### `READY_FOR_REHEARSAL`

- mapping je potvrdený
- rehearsal môže byť spustený

### `BLOCKED_EXTERNAL`

- interný workflow je v poriadku
- externý systém alebo plan limit blokuje ďalší krok

### `BLOCKED_INTERNAL`

- config, payload alebo artifact problém v repo

### `READY_FOR_LIVE_CUTOVER`

- rehearsal má `PASS`
- gate je `GO`
- rollback a notification path sú potvrdené

### `DONE`

- execution vetva je ukončená
- evidence je uložená
