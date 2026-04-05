# Make Failure Output Contract

## Minimálny zlyhaný výstup

```json
{
  "success": false,
  "http_status": "403 | 4xx | 5xx | ''",
  "http_classification": "client_error | server_error | network_error | cloudflare_block",
  "scenario_label": "string",
  "request_decision": "GO | NO_GO",
  "note": "string"
}
```

## Fail podmienky

- `success = false`
- response alebo network stav je zapísaný
- operator vie rozhodnúť retry vs stop
