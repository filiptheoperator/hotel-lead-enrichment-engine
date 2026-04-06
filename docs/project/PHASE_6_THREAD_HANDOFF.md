# Phase 6 Thread Handoff

## Stav projektu

- branch: `main`
- Phase 5: `DONE_INTERNAL`
- Phase 6: `READY_PENDING_EXTERNAL_UNBLOCK`
- ClickUp live path: `PASS`
- Make live API: `BLOCKED_EXTERNAL` (`HTTP 403 / Cloudflare 1010`)

## Najdôležitejšie súbory

- [docs/project/PHASE_5_CLOSEOUT_SUMMARY.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_5_CLOSEOUT_SUMMARY.md)
- [docs/project/PHASE_6_KICKOFF_BRIEF.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_KICKOFF_BRIEF.md)
- [docs/project/MAKE_RESUME_POINT_NOTE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_RESUME_POINT_NOTE.md)
- [docs/project/INTEGRATION_STATUS_SNAPSHOT.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/INTEGRATION_STATUS_SNAPSHOT.md)
- [docs/project/EXTERNAL_BLOCKER_REGISTER.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/EXTERNAL_BLOCKER_REGISTER.md)

## Copy-paste štart pre nový thread

```text
Projekt: Hotel Lead Enrichment Engine OS

Pokračujeme v tom istom repozitári.
Komunikuj iba po slovensky.
Odpovede drž čo najkratšie.

Technické odpovede del presne na:
Diagnóza / VS Code / Codex web / Validácia

Aktuálny stav:
- branch: main
- Phase 5: DONE_INTERNAL
- Phase 6: READY_PENDING_EXTERNAL_UNBLOCK
- ClickUp live path: PASS
- Make API je stále externe blokované cez HTTP 403 / Cloudflare 1010

Source of truth:
- docs/project/PHASE_5_CLOSEOUT_SUMMARY.md
- docs/project/PHASE_6_KICKOFF_BRIEF.md
- docs/project/MAKE_RESUME_POINT_NOTE.md
- docs/project/INTEGRATION_STATUS_SNAPSHOT.md
- docs/project/EXTERNAL_BLOCKER_REGISTER.md

Začni Phase 6 a urob prvých 10 úloh naraz.
```

## Prvých 10 úloh Fázy 6

1. pripraviť controlled live Make run plan
2. pripraviť live output verification checklist
3. pripraviť Make-to-ClickUp execution evidence template
4. pripraviť operator rehearsal script pre execution deň
5. pripraviť live cutover gate decision checklist
6. pripraviť final go-live rollback boundaries
7. pripraviť live success criteria board
8. pripraviť live failure triage sheet
9. pripraviť post-live review template
10. pripraviť Phase 6 readiness summary

## Keď sa odblokuje Make sieť

Pusti len toto:

1. `python3 src/make_id_helper.py --mode teams`
2. `python3 src/make_scenario_test_run.py --mode interface`
3. `python3 src/make_scenario_test_run.py --mode logs`
4. `python3 src/make_scenario_test_run.py --mode run --input-json data/qa/make_input_pack_go.json`
