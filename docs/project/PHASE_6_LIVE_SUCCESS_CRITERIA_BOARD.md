# Phase 6 Live Success Criteria Board

## Board

- Make network access: `PASS` znamená bez `403 / 1010`
- teams check: `PASS` znamená čitateľný výsledok
- interface check: `PASS` znamená čitateľný výsledok
- logs check: `PASS` znamená čitateľný výsledok
- controlled run: `PASS` znamená korektný output contract
- ClickUp verification: `PASS` znamená správny task count a required fields
- incident control: `PASS` znamená žiadny neuzavretý partial write
- evidence completeness: `PASS` znamená vyplnený execution evidence template
- gate discipline: `PASS` znamená bez obídenia `NO_GO`
- post-live review: `PASS` znamená vyplnený review template

## Povinné minimum

- prvé štyri riadky musia byť `PASS` ešte pred controlled run
- `controlled run` nemôže byť `PASS`, ak `request_decision` nie je čitateľný
- `ClickUp verification` nemôže byť `PASS`, ak task count alebo required fields nesedia
- `incident control` nemôže byť `PASS`, ak je otvorený partial write incident

## Celkové pravidlo

- live success = všetky riadky `PASS`
- live blocked = Make sieť alebo externý faktor bráni kontrolovanému runu
- live fail = run prebehol, ale criteria board nemá všetky required `PASS`

## Stav dnes

- board_status: `READY_FOR_USE`
- current_overall: `BLOCKED_EXTERNAL`
- reason: `EXT-MAKE-001`
