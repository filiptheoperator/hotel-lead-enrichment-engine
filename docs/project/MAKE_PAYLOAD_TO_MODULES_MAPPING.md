# Make Payload To Modules Mapping

## Trigger

- prijme celé telo payloadu bez transformácie

## Validator

- číta `decision`
- kontroluje required fields
- pri missing field končí hard stop vetvou

## Router

- `GO` -> ClickUp handoff vetva
- `NO_GO` -> notification / stop vetva

## ClickUp handoff

- číta `clickup_import_csv`
- číta `clickup_import_gate_json`
- číta `run_manifest_json`

## Evidence logger

- zapisuje response status
- zapisuje output reference
- zapisuje operator summary reference
