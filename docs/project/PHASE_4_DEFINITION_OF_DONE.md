# Fáza 4 - Definition of Done

## Fáza 4 je hotová iba keď platí všetko

- existuje kickoff brief pre Fázu 4
- finálny ClickUp API payload contract je uzamknutý
- Make execution payload contract je uzamknutý
- error handling a retry pravidlá sú uzamknuté
- všetky required custom field IDs sú potvrdené v live workspace
- controlled ClickUp rehearsal v reálnom workspace skončil `PASS`
- rehearsal výsledok je zdokumentovaný
- live cutover stop conditions sú jasne pomenované
- žiadna business logika nebola presunutá mimo lokálnej Python pipeline

## Fáza 4 nie je hotová keď platí čo i len jedno

- čo i len jedno required custom pole má `UNVERIFIED_TBD`
- rehearsal je `FAIL` alebo `BLOCKED`
- payload shape sa mení mimo uzamknutého contractu
- Make potrebuje dopĺňať chýbajúce business rozhodovanie
- live write path nie je operatorovi zrozumiteľný

## Aktuálny stav k 2026-04-04

- kickoff brief: hotovo
- ClickUp API payload contract: hotovo
- Make execution payload contract: hotovo
- error handling a retry pravidlá: hotovo
- live custom field IDs: `Neoverené`
- live controlled rehearsal: `Neoverené`

## Záver

Fáza 4 je k dnešnému dňu pripravená na controlled rehearsal, ale ešte nie je uzavretá.
