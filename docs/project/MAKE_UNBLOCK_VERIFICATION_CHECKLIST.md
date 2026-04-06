# Make Unblock Verification Checklist

## Pred prvým retry

1. overiť, že sieť už nevracia `HTTP 403 / Cloudflare 1010`
2. overiť, že sa používa schválený stroj alebo sieť
3. overiť, že env a webhook config ostali bez nechcených zmien
4. overiť, že payload scope sa nemenil
5. overiť, že operator má otvorený Make-unblock run packet
6. overiť, že posledný blocker incident je zdokumentovaný
7. overiť, že evidence log je pripravený
8. overiť, že retry SOP je otvorený podľa typu chyby

## Hard stop

- Cloudflare block stále trvá
- nie je jasné, aký stroj alebo sieť sa používa
- chýba decision log alebo evidence template
