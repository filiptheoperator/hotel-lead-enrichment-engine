# Phase 6 Final Go Live Rollback Boundaries

## Princíp

Rollback ostáva manuálny, nedestruktívny a je dovolený len po potvrdení toho, čo už bolo zapísané.

## Owner model

- rollback owner: `operator + reviewer`
- cleanup bez dvojitého potvrdenia nie je dovolený
- ak nie je reviewer dostupný, batch ostáva `BLOCKED`

## Čo je dovolené

- zastaviť ďalší write
- uzamknúť batch ako `BLOCKED`
- zozbierať task IDs a task URLs
- manuálne označiť scope incidentu
- rozhodnúť o cleanup až po ClickUp kontrole

## Čo nie je dovolené

- automatický hromadný delete bez verifikácie
- retry naslepo bez output review
- pokračovať v ďalšom batchi pri partial write
- prepísať incident ako `PASS`

## Hraničné situácie

- `403` pred write znamená `BLOCKED`, nie rollback
- partial write znamená safe-stop a incident evidence
- nejasný task count znamená stop, kým sa count neuzavrie
- mismatch na required fieldoch znamená `FAIL` a rollback review

## Rozhodovací strom

- bez vytvorených taskov: rollback sa nespúšťa, stav je `BLOCKED` alebo `FAIL`
- s vytvorenými taskmi a čistou evidenciou: najprv review, potom manuálny cleanup alebo ponechanie
- s vytvorenými taskmi a neúplnou evidenciou: okamžitý safe-stop, žiadny cleanup

## Minimum evidence pred rollback rozhodnutím

- task IDs
- task URLs
- run timestamp
- použitý payload
- operator note
- verification note
