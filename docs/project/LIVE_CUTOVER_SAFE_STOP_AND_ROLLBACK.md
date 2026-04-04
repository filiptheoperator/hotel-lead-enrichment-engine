# Live Cutover Safe Stop And Rollback

## Cieľ

Definovať bezpečné zastavenie a rollback postup pre deň live cutover bez deštruktívnych zásahov.

## Safe-stop triggers

- `decision = NO_GO`
- missing required artifact
- external blocker z ClickUp / Make
- partial write risk
- operator nevie potvrdiť, čo už bolo zapísané

## Safe-stop postup

1. zastaviť ďalší write
2. uložiť zoznam už vytvorených taskov alebo write attempts
3. neposielať ďalšie batch riadky
4. poslať failure notification operátorovi
5. označiť batch ako `BLOCKED`, nie ako `DONE`

## Rollback princíp

- rollback je operator-driven
- žiadny automatický destructive cleanup
- najprv skontrolovať, čo už vzniklo v ClickUp
- až potom rozhodnúť o ručnom odstránení alebo ponechaní test taskov

## Minimum rollback evidence

- task IDs
- task URLs
- timestamp incidentu
- error text
- affected batch context
