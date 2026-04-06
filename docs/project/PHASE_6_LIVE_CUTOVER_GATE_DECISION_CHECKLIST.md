# Phase 6 Live Cutover Gate Decision Checklist

## Gate otázky

1. je ClickUp live path stále `PASS`?
2. je `EXT-MAKE-001` odstránený?
3. je payload contract stále `LOCKED`?
4. je operator rehearsal `PASS`?
5. existuje execution evidence template?
6. existuje output verification checklist?
7. je rollback owner jasný?
8. je failure triage sheet pripravený?
9. je post-live review template pripravený?
10. vie operator vysvetliť safe-stop bez domýšľania?

## Hodnotenie otázok

- odpoveď `yes` je povolená len pri explicitnej evidencii alebo otvorenom artefakte
- odpoveď `no` znamená `NO_GO`, ak nejde čisto o stále otvorený external blocker
- stále otvorený Make blocker znamená `BLOCKED`, nie `GO`

## Rozhodnutie

- `GO`: všetky otázky sú `yes`
- `NO_GO`: aspoň jedna otázka je `no`
- `BLOCKED`: Make sieť je stále externe blokovaná

## Zakázané rozhodnutia

- `GO` pri otvorenom `EXT-MAKE-001`
- `GO` bez operator rehearsal
- `GO` bez rollback ownera
- `GO` bez evidence template a output verification checklistu

## Povinný zápis

- decision:
- decided_by:
- timestamp:
- blocker_reference:
- next_review_point:
- evidence_note:
