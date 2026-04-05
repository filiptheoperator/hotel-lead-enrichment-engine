# Make Launch Checklist Minimal

## Pred spustením

1. payload je validný
2. `decision = GO`
3. archive cross-check sedí
4. ClickUp rehearsal je `PASS`
5. Make network blocker je vyriešený
6. safe/no-op guard je nastavený podľa cieľa testu

## Nespúšťať ak

- `NO_GO`
- `HTTP 403`
- `Cloudflare 1010`
- missing artifact
