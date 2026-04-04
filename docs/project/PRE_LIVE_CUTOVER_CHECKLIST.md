# Pre-Live Cutover Checklist

## Predpoklady

- controlled rehearsal má `PASS`
- externé blockery sú vyriešené alebo explicitne akceptované
- Make input validation prešla
- operator pozná safe-stop postup

## Checklist

1. gate rozhodnutie je `GO`
2. required artifacty existujú
3. archive dir existuje
4. ClickUp mapping je potvrdený
5. rehearsal evidence existuje
6. failure notification path je potvrdený
7. rollback owner je jasný
8. operator pozná partial write SOP

## Hard stop

- rehearsal nie je `PASS`
- external blocker ostáva otvorený
- gate nie je `GO`
- chýba rollback owner
