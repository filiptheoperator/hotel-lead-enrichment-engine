# Make Success Output Contract

## Minimálny úspešný výstup

```json
{
  "success": true,
  "http_status": 200,
  "http_classification": "success",
  "scenario_label": "string",
  "request_decision": "GO",
  "note": "string"
}
```

## Pass podmienky

- `success = true`
- `http_status` je `200`, `201` alebo `202`
- `http_classification = success`
