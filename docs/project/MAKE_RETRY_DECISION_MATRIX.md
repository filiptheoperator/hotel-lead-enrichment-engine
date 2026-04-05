# Make Retry Decision Matrix

## Retry now

- `network_error`
- `server_error`

## Neretriovať

- `client_error`
- `cloudflare_block`
- `invalid_payload`
- `no_go_batch`

## Operator akcia

- pri retryable stave použiť existujúci backoff plán
- pri non-retryable stave najprv opraviť príčinu
