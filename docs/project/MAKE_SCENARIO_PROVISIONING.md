# Make Scenario Provisioning

## Cieľ

Spravovať Make scenár z repozitára čo najbližšie k `infrastructure as code`, ale bez novej architektúry.

## Súbory

- [configs/make_api.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_api.yaml)
- [configs/make_scenario_blueprint.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_scenario_blueprint.json)
- [src/make_scenario_deploy.py](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_deploy.py)
- [src/make_scenario_test_run.py](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_test_run.py)
- [docs/project/MAKE_BLUEPRINT_FINALIZATION_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_BLUEPRINT_FINALIZATION_CHECKLIST.md)
- [docs/project/MAKE_PAYLOAD_TO_MODULES_MAPPING.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_PAYLOAD_TO_MODULES_MAPPING.md)
- [docs/project/MAKE_RESPONSE_PARSING_CONTRACT.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_RESPONSE_PARSING_CONTRACT.md)
- [docs/project/MAKE_RETRY_DECISION_MATRIX.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_RETRY_DECISION_MATRIX.md)
- [docs/project/MAKE_LAUNCH_CHECKLIST_MINIMAL.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_LAUNCH_CHECKLIST_MINIMAL.md)
- [docs/project/MAKE_POST_RUN_RECONCILIATION_RULES.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_POST_RUN_RECONCILIATION_RULES.md)
- [docs/project/MAKE_LIVE_CUTOVER_COMMAND_CHECKLIST.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_LIVE_CUTOVER_COMMAND_CHECKLIST.md)
- [docs/project/MAKE_RESUME_POINT_NOTE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_RESUME_POINT_NOTE.md)

## Režimy

1. `plan`
2. `create`
3. `update`
4. `activate`
5. `test_run`

## Dôležité pravidlá

- najprv použi `plan`
- `configs/make_scenario_blueprint.json` je zatiaľ `Neoverené`
- connection IDs a webhook názov sa nesmú hádať
- ak Make vyžaduje manuálny bind connection, treba ho spraviť v UI len raz

## Bezpečný prvý krok

```bash
python3 src/make_scenario_deploy.py --mode plan
```

## Neoverené

- či všetky konkrétne Make moduly v našom scenári pôjdu plne bez manuálneho connection bindu
