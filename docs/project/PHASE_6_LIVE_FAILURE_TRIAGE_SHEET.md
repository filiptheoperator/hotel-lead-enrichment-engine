# Phase 6 Live Failure Triage Sheet

## Triage vstup

- incident_time:
- operator:
- reviewer:
- batch_label:
- stage: `teams | interface | logs | run | clickup_verification`
- visible_error:
- impacted_scope:

## Klasifikácia

- network_block: `yes | no`
- cloudflare_1010: `yes | no`
- make_api_error: `yes | no`
- clickup_write_error: `yes | no`
- partial_write: `yes | no`
- evidence_missing: `yes | no`

## Okamžitá akcia

- stop_further_writes: `yes | no`
- mark_status: `BLOCKED | FAIL`
- notify_owner:
- capture_task_ids:
- capture_task_urls:
- capture_output_file:

## Ďalší krok

- retry_allowed: `yes | no`
- retry_condition:
- rollback_review_needed: `yes | no`
- linked_evidence:
- final_triage_note:

## Rozhodovacie pravidlá

- `BLOCKED`: external blocker alebo network block bráni čitateľnému pokračovaniu
- `FAIL`: run prebehol, ale výsledok je chybný alebo ClickUp verifikácia zlyhala
- `retry_allowed = no`: ak existuje partial write bez uzavretej evidencie
- `rollback_review_needed = yes`: ak vznikli tasky alebo field mismatch
