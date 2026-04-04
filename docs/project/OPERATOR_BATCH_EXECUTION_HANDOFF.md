# Operator Batch Execution Handoff

## Cieľ

Dať operátorovi stručný execution-day handoff pre batch run bez potreby dohľadávať logiku v kóde.

## Pred spustením

- over `run_manifest.json`
- over `clickup_import_gate.json`
- over dry run sample
- over operator decision summary
- ak gate je `NO_GO`, nepokračuj live execution vetvou

## Počas spustenia

- sleduj len artifacty definované v repo
- nerob manuálne prepočty scoringu alebo QA
- ak sa objaví externý blocker, zastav len affected vetvu

## Po spustení

- potvrď, či vznikol archive dir
- potvrď, či bola poslaná správna notifikácia
- pri ClickUp write vetve skontroluj, či nejde o partial write risk

## Operator pravidlo

Ak niečo nie je explicitne potvrdené v artefaktoch, ber to ako `Neoverené`.
