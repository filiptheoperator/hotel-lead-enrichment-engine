# Make Failure Notification Contract

## Cieľ

Zjednotiť minimálny obsah notifikácie pri zlyhaní Make / ClickUp integračnej vetvy.

## Povinné polia notifikácie

- `failure_stage`
- `failure_type`
- `batch_decision`
- `affected_artifact`
- `operator_action`
- `retry_allowed`
- `next_step`

## Failure types

- `missing_required_artifact`
- `invalid_make_payload`
- `no_go_batch`
- `clickup_external_blocker`
- `partial_write_risk`
- `unknown_external_error`

## Notification templates

### Make hard stop

`Batch sa zastavil pred integračným write. Skontroluj required artifacty a gate rozhodnutie.`

### ClickUp external blocker

`ClickUp rehearsal alebo write narazil na externý blocker. Mapping je potvrdený, ale write pokračovanie je zastavené mimo lokálneho workflow.`

### Partial write risk

`Došlo k partial write riziku. Nepokračuj batchom, najprv skontroluj vytvorené tasky a rozhodni o cleanup.`
