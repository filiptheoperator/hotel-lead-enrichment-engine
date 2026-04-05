# Make Response Parsing Contract

## Úspech

- `http_status` je `200`, `201` alebo `202`
- `response_received = true`
- klasifikácia: `success`

## Retry

- klasifikácia: `network_error`
- klasifikácia: `server_error`

## Bez retry

- klasifikácia: `client_error`
- klasifikácia: `cloudflare_block`
- klasifikácia: `invalid_payload`

## Minimálne polia

- `response_received`
- `http_status`
- `http_classification`
- `note`
- `webhook_target`
