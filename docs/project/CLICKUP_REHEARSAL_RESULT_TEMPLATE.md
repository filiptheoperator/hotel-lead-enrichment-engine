# ClickUp Rehearsal Result Template

## Meta

- rehearsal_date:
- operator:
- workspace_name: `90121598651`
- test_list_or_folder: `Acquisition / Pipeline / Target Accounts`
- source_sample_file: `data/qa/clickup_import_dry_run_sample.csv`
- clickup_export_mode: `phase1_minimal`
- rehearsal_status: `BLOCKED`
- workspace_confirmed: `yes`

## Gate context

- batch_gate_decision: `NO_GO`
- allowed_mode: `isolated_test_only`
- execution_note: `Live write sa zastavil na ClickUp plan limite FIELD_033 pri custom field write.`

## Confirmed custom field IDs

| ClickUp field name | Required for cutover | Live field ID | Type confirmed | Result |
| --- | --- | --- | --- | --- |
| `Hotel name` | yes | `8d5d2675-e51f-4e8c-a8a2-1494a8395db2` | `short_text` | `PASS` |
| `City` | yes | `ff8675cf-25c9-4fc3-b9cf-32048655a6e3` | `text` | `PASS` |
| `Priority score` | yes | `51760196-c6d6-4143-bb31-0f587e603fe0` | `short_text` | `PASS` |
| `Contact phone` | no | `47aef14e-21f4-4ec3-b256-5b1b12827c3d` | `phone` | `PASS` |
| `Contact website` | no | `ff8716e8-0bd2-4608-9297-c7617d49fcd2` | `url` | `PASS` |
| `Subject line` | yes | `f3cbaad6-fc27-4b0a-9c9b-9ffc71d0fb67` | `short_text` | `PASS` |
| `Source file` | yes | `093e51a8-0114-4a8c-910c-f7a1950a7318` | `short_text` | `PASS` |

## Sample rows tested

| Row reference | Task created | Name ok | Description ok | Status ok | Priority ok | Required custom fields ok | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `row_1 / Loft Hotel Bratislava` | `869ct12ah` | `PASS` | `UNVERIFIED_AFTER_ERROR` | `PASS` | `PASS` | `BLOCKED` | task vznikol, custom field write zastavil `FIELD_033` |
| `row_2 / Radisson Blu Carlton Hotel, Bratislava` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | nevykonané po hard stop |
| `row_3 / Areál vodných športov Čunovo` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | nevykonané po hard stop |

## Field mismatches

- mismatch_1: ClickUp API vrátil `FIELD_033`
- mismatch_2: custom field write bol zablokovaný plan limitom
- mismatch_3: verification required custom field values neprebehla

## Partial write risk

- partial_write_detected: `yes`
- created_task_refs: `869ct12ah https://app.clickup.com/t/869ct12ah`
- cleanup_needed: `yes`

## Decision

- next_action: `rozhodnúť o cleanup test tasku 869ct12ah a vyriešiť ClickUp custom field usage limit pred ďalším rehearsal retry`
- config_update_needed: `no`
- live_cutover_ready: `no`

## Poznámka

Ak čo i len jedno required pole nemá potvrdený live field ID alebo sample write neprejde, live cutover ostáva `NO_GO`.
