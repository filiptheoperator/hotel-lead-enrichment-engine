# Outbound Copy Disciplines Integration — Hotel Lead Enrichment Engine OS

## Účel
Tento dokument destiluje len tie outbound copy princípy, ktoré sú reálne užitočné pre aktuálny projekt:

**cieľ projektu nie je len písať lepšie emaily**  
Cieľ projektu je:
- zrýchliť hotelový enrichment workflow,
- zachovať vysokú kvalitu reálnych dát o hoteli,
- zlepšiť personalizáciu emailov,
- pripraviť kvalitnejší outreach ešte pred prvým discovery call workflowom,
- zapracovať tieto princípy do architektúry, promptov, schém a dokumentácie.

---

## 1. Čo z pôvodného textu je pre náš projekt skutočne užitočné

### 1.1 Give first
Každý outbound email má začínať malou hodnotou, nie pitchom.

Pre náš projekt to znamená:
- 1 konkrétny postreh z hotelového webu,
- 1 konkrétny signál z rezervácie / kontaktu / recepcie / prevádzky,
- 1 konkrétny digitálny nedostatok alebo zlepšiteľný bod,
- 1 užitočný mini-insight, ktorý pôsobí ako poctivý auditový postreh.

**Nie všeobecný marketingový fluff.**  
**Nie “máme AI riešenie”.**  
**Nie “pomôžeme vám s automatizáciou”.**

### 1.2 Micro-commitment
Cold email nemá tlačiť na veľký záväzok.

Pre náš projekt to znamená:
- nežiadať hneď veľký call,
- nežiadať hneď audit purchase,
- nežiadať hneď veľa času.

Preferované CTA:
- „Ak chcete, pošlem vám krátky prehľad.“
- „Môžem vám poslať 3 stručné postrehy.“
- „Ak chcete, pošlem vám krátke zhrnutie toho, čo som si všimol.“
- „Môžem vám to poslať v krátkej a zrozumiteľnej forme.“

### 1.3 One email = one goal
Každý email má mať len jeden cieľ.

Povolené primárne ciele:
- reply,
- súhlas s prijatím krátkeho prehľadu,
- súhlas s krátkym rozhovorom.

Nepovolené:
- reply + call + audit + demo + viacero CTA naraz.

### 1.4 Human frame
Email musí pôsobiť ako normálna ľudská správa.

Pre náš projekt:
- jednoduchý jazyk,
- prirodzený tón,
- žiadny corporate tón,
- žiadny startupový jazyk,
- žiadny AI hype,
- žiadny technický slovník bez potreby.

### 1.5 Relevance > cleverness
Nepotrebujeme “geniálne copy”.
Potrebujeme:
- presný hotelový kontext,
- konkrétny pozorovateľný problém,
- jemnú relevanciu,
- krátky a dôveryhodný prvý kontakt.

### 1.6 Iteration by data
Email system sa nemá meniť podľa pocitu.

Treba sledovať:
- variant,
- angle,
- CTA typ,
- reply outcome,
- booked-call outcome.

### 1.7 AI len na malé kusy
AI sa nemá používať na vymýšľanie celých emailov od nuly bez opory v dátach.

AI sa má používať na:
- extraction of useful facts,
- krátku personalizačnú vetu,
- give-first insight,
- micro-CTA variant,
- structured angle generation.

---

## 2. Čo sa má zmeniť v našej aktuálnej architektúre

## 2.1 Do enrichment schema pridať tieto polia
Tieto polia majú byť povinnou súčasťou enrichment vrstvy:

- `give_first_insight`
- `main_observed_issue`
- `email_hook`
- `micro_cta`
- `primary_email_goal`
- `proof_snippet`
- `email_angle`
- `cta_type`
- `variant_id`
- `test_batch`
- `reply_outcome`

## 2.2 Email system sa má skladať z blokov
Každý draft emailu má byť skladaný z týchto blokov:

1. `personalization_line`
2. `give_first_line`
3. `relevance_line`
4. `low_friction_cta`

Voliteľne:
5. `proof_line`

## 2.3 Prompty sa musia sprísniť
Všetky email/enrichment prompty musia obsahovať tieto pravidlá:

- Slovak only
- very short output
- one email = one goal
- always include one concrete give-first insight
- use only grounded facts from enrichment
- no invented claims
- no fake scarcity
- no exaggerated revenue promises
- no corporate tone
- no AI jargon
- no startup language
- CTA must be low-friction

## 2.4 Enrichment engine musí dodávať lepší copy-ready output
Enrichment nemá končiť len pri:
- profile hotela,
- kontaktoch,
- prevádzke,
- ClickUp fields.

Musí dodať aj:
- 1 jasný give-first insight,
- 1 najbezpečnejší email hook,
- 1 hlavný pozorovaný problém,
- 1 nízkotlakové CTA,
- 1 krátky proof/relevance snippet,
- 2–3 testovateľné email angles.

## 2.5 CRM / export vrstva musí podporovať testovanie
Do exportov má ísť:
- `email_angle`
- `cta_type`
- `variant_id`
- `test_batch`
- `reply_outcome`

Aby sa dala neskôr merať kvalita.

---

## 3. Čo z pôvodného textu nepoužiť

Toto sa do nášho projektu teraz nemá zavádzať:

- grey hat outbound techniky,
- fake scarcity,
- agresívne guarantees,
- revenue guarantees bez proof,
- príliš salesy authority flexing,
- umelé chyby v texte na vyzeranie “ľudskosti”,
- prehnané offer framing,
- manipulácia cez tlak.

Náš segment je trust-heavy.
Potrebujeme presnosť a pokoj, nie agresívny predaj.

---

## 4. Priame pravidlá pre hotelový outreach layer

### Povinné
- email musí byť krátky,
- email musí byť zrozumiteľný,
- email musí vychádzať z reálnych zistení,
- email musí mať len jeden cieľ,
- email musí ponúknuť malú hodnotu,
- email musí používať prirodzenú slovenčinu.

### Zakázané
- “AI transformation”
- “automation for automation’s sake”
- “booking funnel”
- “conversion optimization”
- “friction in inquiry flow”
- “audit layer”
- “pipeline”
- “personalized growth solution”
- prehnaný expert tón
- korporátne frázy

---

## 5. Presné zmeny, ktoré má Codex spraviť

Codex má:

1. prejsť všetky projektové dokumenty,
2. nájsť všetky miesta, kde sa rieši enrichment, email drafting, workflow, schema alebo architektúra,
3. doplniť tieto copy disciplíny všade tam, kde to dáva zmysel,
4. ak treba, vytvoriť nové doplnkové `.md` súbory,
5. neprepisovať zbytočne celý projekt,
6. robiť len presné a praktické zmeny.

---

## 6. Povinné oblasti, ktoré má Codex upraviť

### A. Project instructions
Doplniť:
- give-first rule
- one email = one goal
- low-friction CTA rule
- no corporate tone
- AI only for small pieces, not full email invention

### B. Master SOP / business SOP
Doplniť:
- outbound copy discipline layer
- relationship between enrichment quality and email quality
- testing discipline for outreach variants

### C. Current architecture / workflow docs
Doplniť:
- new schema fields
- email block system
- testing fields
- copy-ready enrichment outputs

### D. Prompt docs
Doplniť:
- exact copy rules
- output rules
- short Slovak tone rules
- grounded-facts-only rules

### E. Repo / build docs
Doplniť:
- where these fields live in pipeline
- where they move in exports
- where testing happens

---

## 7. Výstup, ktorý má Codex vytvoriť

Minimálne tieto výstupy:

### Povinné
- update existujúcich `.md` súborov
- update prompt dokumentov
- update workflow dokumentácie
- update schema dokumentácie

### Voliteľné, ak treba
- nový `.md` súbor typu:
  - `OUTREACH_COPY_LAYER.md`
  - `EMAIL_DRAFTING_RULES.md`
  - `OUTBOUND_TESTING_SPEC.md`

Codex má vytvoriť len to, čo reálne zlepší projekt.
Nie zbytočný papier.

---

## 8. Definition of done
Úloha je hotová, ak:

- projektové dokumenty už obsahujú copy disciplíny z tohto dokumentu,
- enrichment schema obsahuje nové fields,
- email system je definovaný cez bloky,
- prompts sú upravené,
- workflow dokumentácia je rozšírená,
- testing fields sú zavedené,
- všetko zostáva v slovenčine,
- nič nespadne do hype / fluff / generic marketing language.

---

## 9. Hotový Codex príkaz

Skopíruj a pošli Codexu presne toto:

```txt
Read the entire current project and integrate the outbound copy disciplines from the file `OUTBOUND_COPY_DISCIPLINES_INTEGRATION.md` into the existing architecture, workflow, prompts, schemas, and documentation.

Project rules:
- Slovak only
- keep responses short
- keep instructions beginner-safe
- all technical guidance must stay extremely clear and step-by-step
- do not add fluff
- do not rewrite the whole project unless necessary
- make only practical, architecture-relevant improvements

Your job:
1. scan all existing project `.md` files
2. find all documents related to:
   - project instructions
   - SOP / business logic
   - workflow architecture
   - enrichment engine
   - email drafting
   - prompts
   - schema / exports
3. integrate the following principles where relevant:
   - give first
   - one email = one goal
   - low-friction CTA
   - human tone
   - relevance over cleverness
   - AI only for small copy components
   - testing by data, not gut feeling
4. update existing docs first
5. create additional `.md` docs only if truly needed

Mandatory schema additions:
- give_first_insight
- main_observed_issue
- email_hook
- micro_cta
- primary_email_goal
- proof_snippet
- email_angle
- cta_type
- variant_id
- test_batch
- reply_outcome

Mandatory email block system:
- personalization_line
- give_first_line
- relevance_line
- low_friction_cta
- optional proof_line

Mandatory prompt rules:
- Slovak only
- very short output
- one email = one goal
- always include one concrete give-first insight
- use only grounded facts from enrichment
- no invented claims
- no fake scarcity
- no exaggerated promises
- no corporate tone
- no AI jargon
- no startup language
- CTA must be low-friction

Do not add:
- grey hat tactics
- fake scarcity
- manipulative pressure tactics
- aggressive guarantees
- hype language

Definition of done:
- all relevant docs updated
- schema docs updated
- prompt docs updated
- workflow docs updated
- outreach/email logic improved
- everything remains coherent with the current Hotel Lead Enrichment Engine OS project
- show me exactly which files you changed and why
```

---

## 10. Krátky záver
Tento dokument slúži ako presná integračná vrstva medzi:
- naším hotelovým enrichment workflowom,
- email drafting systémom,
- a disciplínou outbound copy, ktorá je pre nás užitočná bez balastu.

Nepreberáme celý outbound kurz.
Preberáme len to, čo zlepší:
- kvalitu emailov,
- kvalitu enrichment outputu,
- testovanie,
- a praktickú použiteľnosť projektu.
