# Phase 6 Live Output Verification Checklist

## Overiť po Make run

1. success alebo failure output je uložený
2. `scenario_label` sedí s očakávaným scenárom
3. `request_decision` je čitateľný
4. `http_status` je zapísaný
5. `http_classification` je zapísaný
6. response note vysvetľuje výsledok
7. ak bol write pokus, existuje ClickUp verification stopa
8. task count sedí s očakávaním pre daný batch
9. required ClickUp fields sedia
10. partial write je buď `no`, alebo je okamžite evidovaný incident

## PASS pravidlá

- `teams`, `interface` a `logs` majú čitateľný výsledok
- output sedí s [MAKE_SUCCESS_OUTPUT_CONTRACT.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_SUCCESS_OUTPUT_CONTRACT.md) alebo [MAKE_FAILURE_OUTPUT_CONTRACT.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_FAILURE_OUTPUT_CONTRACT.md)
- operator vie ukázať evidenciu
- ClickUp verification nemá mismatch na required poliach
- task count sedí s očakávaním batchu
- partial write je `no`

## STOP pravidlá

- chýba output artifact
- status nie je interpretovateľný
- task count nesedí
- required field mismatch
- partial write bez zoznamu affected taskov
- `request_decision` chýba alebo nie je `GO | NO_GO`
- `http_status` alebo `http_classification` chýba pri failure výstupe

## Klasifikácia výsledku

- `PASS`: všetky required body sú splnené
- `BLOCKED`: Make výsledok je zasiahnutý external blockerom ešte pred čitateľným run výstupom
- `FAIL`: výstup existuje, ale neprejde contract alebo ClickUp verification

## Povinné dôkazy

- run result file
- gate file
- payload reference
- task URLs, ak vznikli tasky
- triage sheet, ak vznikol incident
