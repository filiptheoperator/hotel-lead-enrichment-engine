# Make Orchestration Acceptance Criteria

## Acceptance criteria

1. Make prijme len uzamknutý payload contract
2. pri `NO_GO` nevznikne live write pokus
3. pri missing artifact vznikne hard stop notifikácia
4. pri external blocker sa incident označí správnym failure type
5. pri partial write risk sa flow zastaví
6. archive evidence ostane dostupná
7. Make nepridáva business logiku enrichmentu ani QA
8. Make nemení outbound copy discipliny, iba prenáša existujúce artifacty
9. testing polia pre outreach varianty ostanú zachované v exportoch
10. pri `NO_GO` nevznikne live send ani agresívny CTA push
11. Make scenario provisioning z repa nevytvorí novú business logiku mimo uzamknutého payload contractu
12. blueprint template ostane jasne označený ako `Neoverené`, kým neprejde live deploy test

## Pass condition

Všetkých 10 bodov je potvrdených v test alebo operator scenári.
