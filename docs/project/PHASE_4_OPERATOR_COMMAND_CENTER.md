# Fáza 4 - Operator Command Center

## 1-screen stav

- batch source of truth: `local Python pipeline`
- current branch: `main`
- current phase: `Phase 4`
- readiness: `planning-ready`
- live cutover: `not ready`

## Sleduj vždy tieto artefakty

- [data/qa/run_manifest.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_manifest.json)
- [data/qa/clickup_import_gate.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.json)
- [data/qa/clickup_rehearsal_execution.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_rehearsal_execution.json)
- [docs/project/PHASE_4_READINESS_BOARD.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_4_READINESS_BOARD.md)
- [docs/project/EXTERNAL_BLOCKER_REGISTER.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/EXTERNAL_BLOCKER_REGISTER.md)

## Dnešné rozhodovacie otázky

1. je batch `GO` alebo `NO_GO`?
2. ide o interný problém alebo externý blocker?
3. treba pokračovať v planning artefaktoch alebo v live write vetve?

## Akčný režim

- pri `NO_GO`: nechoď do live execution
- pri externom blockerovi: pokračuj v neblokovaných plánovacích krokoch
- pri partial write: použi cleanup SOP
