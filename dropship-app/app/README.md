# Dropship MVP — app

Pipeline per dropshipping in quattro fasi, con guardrail che impediscono all'automazione
di fare danni:

1. **trends**: rileva prodotti in tendenza e calcola un trend score;
2. **catalog + store**: seleziona i prodotti, calcola prezzo e IVA, genera la scheda (Shopify o sito statico);
3. **campaigns**: prepara bozze di campagne ads con budget limitato e stop-loss;
4. **orders**: inoltra gli ordini pagati al fornitore e recupera il tracking.

**Premessa onesta.** Il dropshipping ha margini sottili e rischi reali: resi, tempi di
consegna, conformità dei prodotti, account ads sospesi. Questo MVP non promette guadagni.
Serve a **non perdere soldi per errore** e a decidere sui numeri: margine dopo IVA e
commissioni, ROAS di break-even, stop-loss.

## Avvio rapido (tutto in mock, nessuna chiave)

```bash
cd dropship-app/app
python3 -m unittest discover -s tests      # suite completa, solo standard library, nessuna rete
python3 -m dropship.cli status             # mostra quali connettori sono MOCK e quali REALI
python3 -m dropship.cli scan               # classifica dei prodotti; mostra i bloccati e il motivo
python3 -m dropship.cli publish            # crea le richieste di approvazione (nulla viene pubblicato)
python3 -m dropship.cli pending            # elenca le richieste in attesa
python3 -m dropship.cli approve <id> --by "Nome Cognome"   # approvazione UMANA
python3 -m dropship.cli publish            # pubblica gli approvati + sito statico in data/site/
python3 -m dropship.cli campaign --budget 10   # bozze in PAUSA + richieste di attivazione
#   approva le attivazioni, poi rilancia `campaign`: le campagne si attivano e parte lo stop-loss
python3 -m dropship.cli campaign --raise-id CMP-xxxx --to 15   # aumento budget: serve approvazione
python3 -m dropship.cli orders             # inoltro ordini pagati + tracking (l'ordine non pagato viene rifiutato)
python3 -m dropship.cli kill on --reason "..."   # kill switch: blocca tutto e mette in pausa le campagne
python3 -m dropship.cli kill off
```

Lo stato è salvato in file JSON sotto `data/` (o `DROPSHIP_DATA_DIR`), con permessi `0600`.

## Architettura

```
dropship/
  config.py         soglie, pricing, cap: default + override da env, validati (config assurda = errore all'avvio)
  models.py         dataclass di dominio (nessuna dipendenza)
  http.py           client JSON su urllib: solo HTTPS, timeout, nessun redirect, errori senza segreti
  secrets_util.py   Secret: nasconde le chiavi in repr, str e log
  adapters.py       factory: adapter REALE se ci sono tutte le chiavi, altrimenti MOCK
  trends/           sources.py (Mock, SerpApi + Meta Ad Library), scoring.py, service.py (scan)
  catalog/          pricing.py (IVA, commissioni, margine minimo, ROAS di break-even), selection.py
  store/            copywriter.py (Mock, Anthropic), listing.py (payload Shopify), publishers.py (Mock, Shopify),
                    static_site.py (fallback HTML), service.py (pubblicazione con guardrail)
  campaigns/        planner.py (cap budget, stop-loss), platforms.py (Mock, Meta, TikTok, Google), service.py
  orders/           suppliers.py (Mock, CJdropshipping), service.py (validazione, idempotenza, tracking)
  guardrails/       compliance.py, approvals.py, spend.py, killswitch.py
  cli.py            scan | publish | campaign | orders | approve | reject | pending | kill | status
```

Flusso: `Supplier.search_products` → `TrendSource.get_signal` → `score_candidate` →
`select_products` (conformità + pricing) → `publish_product` (testi → controllo testi →
approvazione → store) → `CampaignManager` (bozza in pausa → approvazione → attiva →
stop-loss) → `OrderService.forward` → `get_tracking`.

Ogni connettore esterno ha **un'interfaccia astratta, un adapter MOCK e un adapter REALE**.
Il core usa solo la standard library; l'unica dipendenza opzionale è `anthropic`, importata
solo quando la chiave è presente. Se manca il pacchetto, l'app usa il copywriter mock.

### Decisioni principali (ADR sintetici)

| Decisione | Motivo | Alternativa scartata |
|---|---|---|
| Solo stdlib (urllib, dataclass, json) | test senza installare nulla, superficie d'attacco minima | requests/pydantic: dipendenze in più nel core |
| Stato su file JSON | MVP a utente singolo, semplice da ispezionare | DB: prematuro |
| Adapter iniettabili (`transport`, `client`) | test degli adapter reali senza rete | mock globali di urllib |
| Fail-closed sui dati mancanti | mai decidere su numeri inventati | stime di default |
| Campagne sempre create in pausa | la spesa parte solo dopo approvazione umana | attivazione automatica |

## Trend score

Il punteggio va da 0 a 100 ed è la somma pesata di cinque componenti: crescita della domanda (30%),
saturazione ads inversa (20%), margine stimato al prezzo di mercato (25%), peso e spedizione (10%),
stagionalità (15%). Ogni soglia in `.env` (`DROPSHIP_MIN_*` / `DROPSHIP_MAX_*`) è **bloccante**:
basta violarne una per scartare il prodotto, qualunque sia il punteggio. Se manca la crescita, la
saturazione o il prezzo di mercato, il prodotto risulta `DATO MANCANTE` e viene scartato. La sola
stagionalità mancante viene considerata neutra, e il motivo viene comunque indicato.

## Pricing e IVA

`netto = P/(1+IVA)`, `fee = P·fee% + fisso`, `profitto = netto − costo − spedizione − fee`,
`margine = profitto/netto`. Il prezzo minimo che garantisce `DROPSHIP_MIN_MARGIN` si ottiene
risolvendo l'equazione per P, poi si arrotonda per eccesso a X,90. Se il prezzo di mercato
rispetta il margine minimo, si usa quello. ROAS di break-even = `P / profitto`.

## Guardrail (ogni regola ha un test in `tests/test_guardrails.py` e negli altri test di modulo)

| Regola | Dove |
|---|---|
| Categorie vietate: armi, integratori, farmaci, dispositivi medici, tabacco/svapo, adulti, droghe | `compliance.check_product` |
| Parole vietate nel titolo o nella descrizione (match su parole intere: "armadio" non è "arma") | idem |
| Cosmetici solo con CPNP + Persona Responsabile UE; elettronica, giocattoli e infanzia solo con CE | idem |
| Marchi protetti o "replica"/"fake" senza autorizzazione del titolare: bloccati | idem |
| Testi con claim sanitari o garanzie assolute ("cura", "garantito al 100%"): bloccati | `compliance.check_copy` |
| Approvazione umana obbligatoria per pubblicare un prodotto, attivare una campagna o alzare un budget | `approvals.ApprovalStore` |
| Ogni approvazione vale per un solo soggetto esatto (es. `CMP-1:15.00`) e una sola esecuzione | idem (`consume`) |
| Cap per campagna e cap giornaliero totale (le bozze in pausa prenotano budget) | `spend.SpendGuard` |
| Stop-loss: pausa se ROAS < break-even dopo una spesa minima; con meno spesa: `DATI INSUFFICIENTI` | `campaigns.planner` |
| Kill switch (file o env) blocca pubblicazioni, campagne e ordini; `kill on` mette in pausa tutto | `killswitch.KillSwitch` |
| Mai ordinare al fornitore prima dell'incasso; SKU solo nostri; quantità 1–10; indirizzo completo | `orders.service` |
| Ordini idempotenti (mai inoltrati due volte); nessun dato personale nello stato o nell'output | idem |

Le liste di conformità sono un **punto di partenza prudente, non una consulenza legale**.
Vanno riviste per il proprio mercato (GPSR, RAEE, etichettatura, ecc.).

## Cosa è mock e cosa è reale

| Connettore | Mock (default) | Reale (chiavi in `.env`) |
|---|---|---|
| Fornitore | catalogo di 9 prodotti dimostrativi, di cui 4 volutamente vietati o non conformi | CJdropshipping API v2 (`CJ_API_KEY`, `CJ_USD_EUR_RATE`) |
| Trend | segnali fissi dimostrativi | SerpApi Google Trends + Google Shopping (`SERPAPI_API_KEY`), Meta Ad Library (`META_AD_LIBRARY_TOKEN`) |
| Store | in memoria + sito statico in `data/site/` con banner "MOCK" | Shopify Admin REST (`SHOPIFY_STORE_DOMAIN`, `SHOPIFY_ADMIN_TOKEN`) |
| Ads | campagne in memoria, metriche deterministiche finte | Meta Marketing API, TikTok Business API v1.3, Google Ads API REST |
| Testi | template | Anthropic Messages API, modello `claude-opus-5-5` (`ANTHROPIC_API_KEY` + `pip install anthropic`) |

Ogni dato mock porta `source="MOCK"`, visibile in CLI, nei tag Shopify (`source:MOCK`) e
nel banner del sito statico. **Gli adapter reali sono testati solo con transport finti:
nessuna chiamata vera è stata eseguita.** Prima di usarli in produzione bisogna verificare
endpoint, versioni API e campi sulla documentazione ufficiale di ciascun servizio, ad esempio
la versione Graph di Meta, la versione Google Ads e le metriche di TikTok.
Conviene partire con budget minimi.

Limiti noti degli adapter reali:
- CJ restituisce prezzi in USD. Senza `CJ_USD_EUR_RATE` la ricerca fallisce di proposito,
  invece di inventare un tasso di cambio.
- Se Google Shopping trova meno di 3 prezzi, il prezzo di mercato resta `DATO MANCANTE`.
- SerpApi richiede la chiave nella query string. Gli errori non stampano mai l'URL.
- La campagna Google viene creata come Search in pausa. Per andare live servono ancora gruppi
  di annunci, annunci e conversioni, da completare nel pannello.

## Segreti e sicurezza

- Nessuna chiave nel codice: un test scansiona i sorgenti alla ricerca di pattern di chiavi.
  `.env` è in `.gitignore` e c'è anche un test che lo verifica.
- Ogni chiave è racchiusa in `Secret`, quindi `repr`, `str` e i log mostrano solo `***`.
  Le chiavi viaggiano solo negli header, tranne SerpApi.
- Il client HTTP accetta solo HTTPS, ha un timeout e non segue i redirect, così i token non
  finiscono su un altro host. I messaggi d'errore riportano solo il codice HTTP.
- Il dominio Shopify viene validato (`*.myshopify.com`, contro l'SSRF). Gli ID di Meta,
  TikTok e Google devono essere numerici e i resource name GAQL vengono validati contro
  l'injection.
- I testi del fornitore e dell'LLM vengono escapati in HTML. Il sito statico ha una CSP senza
  script e nomi file ricavati da slug, con controllo anti path-traversal.
- All'LLM arrivano solo dati prodotto, segnalati come "dati e non istruzioni". Il risultato
  passa comunque da `check_copy`.
- Il nome del cliente viene mascherato nel `repr`. In `orders.json` non c'è nessun dato
  personale e la CLI non stampa indirizzi né email.
- Chi può eseguire `approve` sulla macchina può approvare: proteggi l'accesso alla shell e la
  cartella `data/`.

## Prossimi passi

- un ordine reale di prova verso CJ con budget minimo e account sandbox, dove esistono;
- i webhook Shopify al posto del polling degli ordini;
- un report giornaliero di spesa reale contro il cap e un allarme che attiva il kill switch in automatico.
