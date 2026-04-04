# Make Orchestration Acceptance Criteria

## Acceptance criteria

1. Make prijme len uzamknutý payload contract
2. pri `NO_GO` nevznikne live write pokus
3. pri missing artifact vznikne hard stop notifikácia
4. pri external blocker sa incident označí správnym failure type
5. pri partial write risk sa flow zastaví
6. archive evidence ostane dostupná
7. Make nepridáva business logiku enrichmentu ani QA

## Pass condition

Všetkých 7 bodov je potvrdených v test alebo operator scenári.
