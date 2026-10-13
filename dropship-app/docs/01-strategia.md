# 01 — Strategia: verdetto del board, modello di business, offerta, pricing, piano

> **Stato del documento.** Bozza di strategia scritta *prima* di spendere un euro.
> Ogni numero è un'**IPOTESI** (da sostituire con preventivi, listini e test reali)
> o il risultato di un calcolo su quelle ipotesi (`02-unit-economics.md`).
> Non è consulenza finanziaria, fiscale o legale.
>
> **Ipotesi di partenza dichiarate**
> - Fondatore: una persona sola, senza dipendenti, con ore limitate (IPOTESI: 15–20 h/settimana nei primi 6 mesi).
> - Budget iniziale: **2.000 €** (IPOTESI, centro della forchetta 1.000–3.000 €). Con 1.000 € il piano sotto si accorcia a un solo ciclo di test; con 3.000 € se ne fanno due.
> - Mercato: Italia per primo, poi UE. Nicchia: **non ancora scelta** (è la prima decisione da prendere, vedi §6).
> - Canale di vendita: store proprio (es. Shopify) + ads a pagamento (Meta/TikTok/Google).
>
> **Metodo.** Skill del pacchetto *founder*: board (3 lenti), offer, pricing, CFO
> (`unit_economics.py`), ops, consumer, plan. Limiti onesti:
> - il board è stato applicato **in linea** da un solo agente, non da tre sub-agenti indipendenti: le divergenze tra lenti sono reali ma meno "indipendenti" di quanto il metodo preveda;
> - il **panel consumatori non è stato eseguito** (serve una nicchia e un pitch concreti; vedi §5.5): nessun tasso di acquisto è citato;
> - la curva prezzi Van Westendorp **non è stata calcolata** (dipende dal panel o da un sondaggio reale): nessuna "fascia di prezzo accettabile" è inventata;
> - nessuna ricerca prezzi concorrenti è stata fatta: i concorrenti citati sono categorie/esempi da verificare.

---

## 1. L'idea (scheda "idea file")

- **Cos'è:** un'app che rileva prodotti in tendenza, genera scheda prodotto/store e campagne, e gestisce gli ordini in dropshipping con la massima automazione possibile.
- **Per chi:** (a) consumatori italiani/UE che comprano d'impulso da ads social — se l'app serve uno store proprio; oppure (b) altri dropshipper — se l'app diventa un SaaS.
- **Cosa vende, a che prezzo:** prodotti fisici a 30–50 € IVA inclusa (IPOTESI) con margine lordo ~3x sul costo sbarcato; oppure abbonamento SaaS (prezzo da definire).
- **Dove e come:** online, acquisizione via ads a pagamento, consegna dal fornitore al cliente.
- **Budget e vincoli:** 2.000 € (IPOTESI), una persona, nessun magazzino.

---

## 2. Verdetto del board

### 2.1 Lente "Offerte" (framework di *$100M Offers*)
**Punteggio: 4/10 — Voto: FINANZIARE SE (FUND IF)**

- **Cosa è forte:** il mercato degli acquisti d'impulso online esiste ed è raggiungibile con le ads; i costi di partenza sono bassi; la velocità di test è alta.
- **Cosa lo ucciderebbe (i 3 più pericolosi):**
  1. **Prodotto-commodity senza offerta.** Se lo stesso articolo è su Amazon/AliExpress/Temu a una frazione del prezzo, il cliente lo scopre in 10 secondi: l'unico differenziale diventa il prezzo, e su quello si perde.
  2. **Probabilità percepita bassa.** Tempi di spedizione lunghi, nessuna recensione vera, store appena nato: il cliente non crede che il pacco arriverà. È il punto dove le offerte di dropshipping falliscono di solito.
  3. **Mercato scelto per "trend" invece che per "dolore + soldi + raggiungibilità".** Un prodotto virale non è un mercato.
- **Domande al fondatore:** chi esattamente ha il problema e la capacità di spesa? Perché dovrebbe crederti? In quanti giorni riceve il pacco? Qual è la garanzia?
- **Condizioni:** scegliere una nicchia con dolore reale e acquisti ripetuti; costruire un'offerta (bundle, guida d'uso, garanzia sostenibile) che non sia "lo stesso articolo di AliExpress con ricarico"; consegna ≤ 7 giorni lavorativi.

### 2.2 Lente "Monopolio" (framework di *Zero to One*)
**Punteggio: 2/10 — Voto: NON FINANZIARE (PASS) come pensata oggi**

- **Cosa è forte:** l'idea di un piccolo mercato da dominare è compatibile con una micro-nicchia italiana (lingua, servizio clienti in italiano, fornitore UE).
- **Cosa lo ucciderebbe:**
  1. **Nessun segreto, nessuna difendibilità.** I segnali di tendenza (librerie inserzioni pubbliche, centri creativi delle piattaforme, Google Trends, classifiche dei marketplace) sono visibili a tutti. Quando un prodotto "è in tendenza" è già, per definizione, osservato da migliaia di concorrenti: la rilevazione automatica non è un vantaggio 10x, è il punto di partenza di tutti.
  2. **Copia in una settimana.** Uno store di dropshipping si clona in un giorno: stesso fornitore, stesse foto, stesso video.
  3. **Distribuzione affittata.** Il 100% dei clienti arriva da piattaforme (Meta/TikTok/Google) che possono alzare i costi o sospendere l'account senza preavviso. Non c'è canale proprio.
- **Il SaaS per altri dropshipper** è un mercato già affollato di strumenti di product research, import ordini e automazione (esistono da anni prodotti consolidati in queste categorie; da censire con `/founder-competitors` prima di qualsiasi decisione).
- **Domande:** qual è il piccolo mercato che puoi possedere? Cosa sai tu che gli altri non sanno? Cosa impedisce a un concorrente di copiarti al sesto mese?
- **Perché PASS:** come "app generalista di trend + store generalista" non ha nessuna delle quattro difese (tecnologia 10x, effetti di rete, economie di scala, brand). Il voto cambierebbe verso FUND IF solo per la versione "brand di nicchia" (§2.5).

### 2.3 Lente "Prodotto" (dalla biografia di Steve Jobs di Isaacson)
**Punteggio: 5/10 — Voto: FINANZIARE SE (FUND IF)**

- **Cosa è forte:** l'automazione delle parti ripetitive (schede, varianti creative, tracking, email) libera tempo per le parti che contano.
- **Cosa lo ucciderebbe:**
  1. **Fa troppe cose.** Trend detection + generatore store + generatore campagne + order routing + customer care automatico: cinque prodotti, una persona. Nessuno sarà fatto bene.
  2. **L'esperienza ha giunture che non controlli.** Il cliente vede il tuo store, poi un pacco anonimo dalla Cina con un'etichetta diversa, dopo 12 giorni, con istruzioni in inglese. Ogni passaggio tra sistemi (store → fornitore → corriere) è dove l'esperienza si rompe, e il cliente incolpa te (e legalmente sei tu il venditore).
  3. **Qualità invisibile tagliata.** Il prodotto non è mai stato toccato dal fondatore: nessun controllo qualità, foto non rappresentative.
- **Domande:** qual è l'unica cosa che lo store deve fare benissimo? Com'è il primo minuto del cliente con il prodotto in mano?
- **Condizioni:** campioni ordinati e provati prima del lancio; un solo prodotto/linea per volta; packaging e inserto in italiano dove il fornitore lo consente.

### 2.4 Sintesi del presidente

**Voto: 2 FUND IF, 1 PASS. Punteggio medio: 3,7/10.**

**Rischi sollevati da più lenti (vanno per primi):**
1. **Zero difendibilità / saturazione** (Offerte + Monopolio): i prodotti "di tendenza" sono già saturi quando li vedi.
2. **Esperienza di consegna fuori controllo** (Offerte + Prodotto): tempi lunghi → reclami → rimborsi → chargeback → blocco pagamenti.
3. **Troppo perimetro per una persona** (Prodotto + Monopolio): costruire un SaaS *e* gestire uno store *e* scrivere l'app.

**Disaccordo da conservare:** la lente Offerte pensa che un'offerta forte possa rendere profittevole anche un prodotto non difendibile per qualche mese; la lente Monopolio pensa che senza difese i margini vengano erosi comunque e che il lavoro migliore sia costruire un *brand* (unica difesa accessibile a un singolo). Entrambe hanno ragione su orizzonti diversi.

**Checklist delle condizioni (da spuntare nel resto del lavoro):**
- [ ] Nicchia scelta su "dolore + capacità di spesa + raggiungibilità + acquisto ripetuto", non su "virale" (§6, settimana 1–2).
- [ ] Contribuzione per ordine positiva **dopo** CPA e resi con preventivi reali (`02-unit-economics.md`).
- [ ] Break-even ROAS calcolato e ROAS reale misurato sopra soglia su almeno 50 ordini prima di scalare.
- [ ] Fornitore con consegna UE ≤ 7 giorni lavorativi e responsabile UE ai fini GPSR (`03-operazioni-e-compliance.md`).
- [ ] Campioni ricevuti e provati per ogni prodotto messo in vendita.
- [ ] Offerta costruita contro le obiezioni reali (§4), garanzia solo se il CFO la regge.
- [ ] Un solo prodotto/linea per volta; SaaS **congelato** finché lo store non supera i gate (§3.4).
- [ ] Panel consumatori + test reale (pre-vendita o landing con prezzo) prima di scalare la spesa.

**La versione più forte che il board vede (diversa da quella proposta):** non un'"app che trova trend e vende da sola", ma un **piccolo brand verticale italiano in una micro-nicchia** (un problema specifico di un pubblico specifico), con fornitore a magazzino UE, offerta curata e servizio in italiano. L'app diventa lo **strumento interno** del fondatore: accelera ricerca, schede, varianti creative e operazioni ripetitive, con un umano che approva ogni passaggio rischioso. Il SaaS è un'opzione *futura* da riconsiderare solo se lo strumento interno dimostra, sui numeri dello store, di produrre un vantaggio misurabile.

---

## 3. I rischi veri (senza addolcire)

| Rischio | Perché è concreto | Impatto | Mitigazione |
| --- | --- | --- | --- |
| **Margini sottili** | Nello scenario base la contribuzione è ~1 € per ordine dopo ads e resi (IPOTESI, vedi doc 02). Una piccola variazione di CPA la rende negativa. | Alto | Prezzo ≥ ~3x costo sbarcato, bundle per alzare lo scontrino, stop rapido dei prodotti sotto break-even ROAS. |
| **Chargeback e dispute** | Spedizioni lente generano dispute "articolo non ricevuto"/"non conforme". Ogni disputa costa la commissione del processore (IPOTESI 15–20 €, da verificare sul listino) oltre al rimborso. Superare le soglie di monitoraggio dei circuiti carte (nell'ordine dell'1% delle transazioni, da verificare) porta a riserve o chiusura. | Molto alto | Tracking proattivo, rimborso rapido prima che il cliente apra la disputa, descrittore di addebito riconoscibile, consegne UE. |
| **Tempi di spedizione** | Da Cina senza magazzino UE: tipicamente settimane, con rischio di dazi/IVA all'arrivo se non si usa l'IOSS. Il Codice del Consumo impone consegna entro 30 giorni salvo diverso accordo e tempi dichiarati prima dell'acquisto. | Alto | Fornitore con stock UE; tempi di consegna onesti in pagina prodotto e checkout. |
| **Ban/sospensione account ads** | Meta, TikTok e Google sospendono spesso account nuovi di e-commerce per "pratiche commerciali inaccettabili", feedback negativo dei clienti, "misrepresentation" (Google Merchant Center). L'appello richiede un umano e può durare settimane. | Molto alto (blocca il 100% delle vendite) | Store con dati aziendali completi, policy chiare, niente claim esagerati, account business verificato, warm-up graduale, due canali e una lista email propria. |
| **Blocco Stripe/PayPal/Shopify Payments** | Verifica KYC, riserve sui fondi, trattenute sui nuovi venditori, chiusure per alto tasso di dispute o per categorie a rischio. Il denaro delle vendite può restare bloccato mentre ads e fornitori vanno pagati subito. | Molto alto (cassa) | KYC completo dall'inizio, metodo di pagamento di riserva, riserva di cassa dedicata (doc 02 §6). |
| **Saturazione** | I prodotti visibili come "trend" sono gli stessi che vede chiunque usi gli stessi strumenti; la vita commerciale di un prodotto virale è breve e il CPA sale man mano che entrano concorrenti. | Alto | Nicchia + brand + offerta; trattare la trend detection come input, non come vantaggio. |
| **Compliance UE (GPSR, garanzia 2 anni, IVA)** | Il dropshipper è **il venditore** verso il consumatore: risponde della garanzia legale, della sicurezza del prodotto, delle informazioni obbligatorie. Un fornitore extra-UE senza responsabile UE rende il prodotto non commercializzabile. | Alto | Checklist compliance per prodotto (doc 03) **prima** della messa online. |
| **Tempo del fondatore** | Supporto clienti, dispute, appelli, test creativi, contabilità: non sono passivi. | Medio-alto | Automazione del ripetitivo + regole di escalation; non aprire due business insieme. |

### 3.1 Il mito "totalmente automatizzato + guadagno passivo"

Va ridimensionato, con argomenti:

1. **Le decisioni che contano non sono automatizzabili in sicurezza.** Scegliere un prodotto sicuro e conforme, approvare un claim pubblicitario, decidere un rimborso conteso, rispondere a una disputa, fare appello a un ban, firmare il KYC: sono atti con responsabilità legale del titolare (doc 03 §2).
2. **Il venditore risponde per legge.** Recesso 14 giorni, garanzia legale 2 anni, GPSR, GDPR: ricadono sul titolare della partita IVA, non sull'app né sul fornitore.
3. **La parte "automatica" è la più copiabile.** Se un software può fare tutto da solo, chiunque con lo stesso software fa lo stesso: il margine va verso zero. Ciò che resta difendibile (scelta della nicchia, qualità, brand, servizio) richiede giudizio umano.
4. **Le piattaforme puniscono proprio l'automazione cieca.** Creatività generate in massa, claim non verificati, store "clone" sono tra le cause più comuni di sospensione.
5. **I numeri non lo sostengono nello scenario base.** Con le IPOTESI del doc 02, lo scenario base perde denaro nel primo anno; solo l'ottimistico è positivo, ed è anche il meno probabile.

**Formulazione onesta:** *"Uno store gestito da una persona, con le operazioni ripetitive automatizzate e un umano che approva le decisioni rischiose. Richiede ore ogni settimana. Può non guadagnare nulla: il budget iniziale va considerato capitale di rischio."*

---

## 4. Modello di business: store singolo vs. SaaS

### 4.1 Opzione A — Store singolo (il fondatore vende ai consumatori)

| | |
| --- | --- |
| **Chi paga** | Consumatori finali IT/UE |
| **Ricavo** | Margine sui prodotti (scontrino IPOTESI 39,90 € IVA incl.) |
| **Pro** | Partenza con 1–3 k€; feedback in giorni; insegna al fondatore cosa serve davvero all'app; l'app può restare un insieme di script interni |
| **Contro** | Margini sottili, rischio ban/chargeback, compliance prodotto, lavoro operativo continuo |
| **Difendibilità** | Bassa per uno store generalista; media se diventa brand di nicchia |

Due varianti:
- **A1 generalista "trend-chasing"** (un prodotto virale dopo l'altro): sconsigliato. Massima esposizione a saturazione, ban, chargeback; nessun asset che si accumula.
- **A2 brand di micro-nicchia** (una linea coerente per un pubblico preciso, acquisti ripetuti, lista email): **raccomandato**. Più lento, ma ogni cliente e ogni recensione vera restano.

### 4.2 Opzione B — SaaS per altri dropshipper

| | |
| --- | --- |
| **Chi paga** | Altri dropshipper (abbonamento mensile) |
| **Ricavo** | Ricorrente, margine lordo software alto |
| **Pro** | Nessun rischio prodotto/GPSR/chargeback verso consumatori; ricavo ricorrente; scalabile |
| **Contro** | Mercato già affollato da strumenti consolidati; clienti con alto churn (molti dropshipper smettono dopo pochi mesi); costo di sviluppo e supporto per una persona; serve **credibilità** ("perché il tuo tool trova prodotti vincenti se tu non vendi?"); dipendenza dalle API di Shopify/piattaforme e dai loro termini sui dati (scraping delle librerie inserzioni e dei marketplace può violare i ToS) |
| **Difendibilità** | Bassa se i dati sono pubblici; media solo con dati proprietari (es. risultati reali aggregati, con consenso) |

Ordine di grandezza (IPOTESI, solo per illustrare la dinamica): a 29 €/mese, per 1.500 €/mese di ricavo servono ~52 clienti paganti; con un churn mensile del 10% bisogna acquisirne ~5 nuovi al mese solo per restare fermi. Il CAC in questo mercato è da misurare, non da indovinare.

### 4.3 Opzione C — Ibrido sequenziale (la raccomandazione)

1. **Fase 1 (mesi 0–6): store A2** con l'app come **strumento interno** (solo le funzioni che fanno risparmiare ore misurabili).
2. **Gate per riaprire il SaaS** (tutti veri):
   - lo store ha contribuzione positiva dopo ads e resi per 3 mesi consecutivi;
   - l'app ha prodotto almeno un vantaggio misurabile (es. tempo di lancio prodotto, ROAS dei prodotti selezionati vs. non selezionati);
   - almeno 10 dropshipper reali hanno chiesto/pre-pagato l'accesso dopo aver visto i risultati.
3. Se i gate non passano, il SaaS non si fa: l'app resta uno strumento personale.

**Raccomandazione:** **Opzione C**, partendo da **A2 (brand di micro-nicchia)**. Motivo: è l'unico percorso compatibile con 2.000 € e una persona, e produce i dati che servirebbero anche al SaaS. Il SaaS subito significherebbe vendere "pale per cercare l'oro" senza aver mai scavato, in un mercato già pieno di pale.

---

## 5. L'offerta (metodo *founder-offer*)

> Il panel non è stato eseguito: la lista problemi qui sotto è costruita dalle obiezioni tipiche dell'acquisto da store sconosciuto via ads (IPOTESI) e va riscritta con le obiezioni reali del panel/test della nicchia scelta.

### 5.1 Lista problemi (dal punto di vista del cliente)

Prima dell'acquisto:
1. "Non conosco questo sito, sarà una truffa?"
2. "Su Amazon/Temu c'è uguale a meno."
3. "Le recensioni sembrano finte."
4. "Non so se funziona davvero per il mio caso."
5. "Quanto ci mette ad arrivare?"
6. "Se non mi piace, come lo restituisco e chi paga?"
7. "Mi arriveranno dazi o costi alla consegna?"
8. "Devo creare un account / dare troppi dati."

Durante l'attesa:
9. "Non so dov'è il pacco."
10. "Il tracking non si aggiorna."
11. "Il servizio clienti non risponde / risponde un bot in inglese."

Dopo la consegna:
12. "È diverso dalle foto."
13. "Istruzioni solo in inglese/cinese."
14. "Si è rotto dopo un mese: a chi mi rivolgo?"
15. "Mi serve il ricambio/accessorio e non si trova."
16. "Non so come usarlo al meglio."
17. "Ricevo troppe email promozionali."
18. "Il rimborso tarda."

### 5.2 Soluzioni, valore e costo (1–5)

| # | Soluzione | Valore | Costo | Tenere? |
| --- | --- | :-: | :-: | --- |
| 1, 6 | Pagina "chi siamo" con ragione sociale, P.IVA, sede, telefono/email reali; policy resi chiara | 5 | 1 | Sì (è anche un obbligo, doc 03) |
| 2 | Bundle/kit esclusivo + guida d'uso in italiano (ciò che il marketplace non dà) | 4 | 2 | Sì |
| 3 | Solo recensioni verificate di acquirenti reali; nessuna importata | 4 | 1 | Sì (obbligo Omnibus) |
| 4 | Pagina "per chi è / per chi NON è" | 4 | 1 | Sì |
| 5, 7 | Spedizione da magazzino UE, tempi dichiarati, nessun costo alla consegna | 5 | 3 | Sì (condizione del board) |
| 9, 10 | Email/SMS di tracking automatiche in italiano | 4 | 1 | Sì (automatizzabile) |
| 11 | Supporto in italiano entro 24 h lavorative (bozza AI + approvazione umana) | 5 | 2 | Sì |
| 12 | Foto/video dai campioni reali, non dal fornitore | 4 | 2 | Sì |
| 13, 16 | Mini-guida PDF/video in italiano | 3 | 1 | Sì, come bonus |
| 14 | Garanzia legale 2 anni spiegata in chiaro (è comunque dovuta) | 4 | 1 | Sì |
| 6 | Reso gratuito oltre i 14 giorni di legge | 4 | 4 | **No nello scenario base** (vedi 5.4) |
| 15 | Ricambi in catalogo | 3 | 3 | Più avanti |
| 17 | Frequenza email dichiarata, disiscrizione in un clic | 2 | 1 | Sì |
| 18 | Rimborso entro 5 giorni dal rientro (legge: entro 14 dal recesso) | 4 | 1 | Sì |

### 5.3 Lo stack

- **Il cuore:** non "il prodotto X", ma il risultato per quel pubblico (es. *"Il kit completo per <risultato> in <tempo>, spiegato in italiano"*). Si definisce dopo la scelta della nicchia.
- **Bonus (2–3, ognuno contro un'obiezione):** guida d'uso in italiano (obiezioni 4, 13, 16); accessorio complementare nel bundle (obiezione 2); supporto in italiano con tempi dichiarati (obiezioni 1, 11).
- **Garanzia:** la **garanzia legale di 2 anni** e il **recesso di 14 giorni** sono obblighi, non bonus: vanno comunicati con chiarezza, **senza presentarli come un regalo** (presentare diritti di legge come vantaggio distintivo è una pratica commerciale ingannevole). Una garanzia *convenzionale* aggiuntiva (es. "30 giorni soddisfatti o rimborsati") solo se i numeri la reggono (5.4).
- **Urgenza/scarsità:** solo vere (prima produzione limitata realmente, finestra di lancio con data di fine). Nessun countdown finto, nessun "solo 3 rimasti" inventato, nessun prezzo barrato mai praticato.
- **Il nome:** dell'offerta, non dell'azienda; da scegliere con la nicchia.

### 5.4 Quanto costa la garanzia estesa (calcolo su IPOTESI)

Una garanzia "30 giorni soddisfatti o rimborsati con reso gratuito" fa perdere, su ogni reclamo, prodotto + spedizione + fee + CPA (non recuperabili) ≈ 8,00 + 5,50 + 1,20 + 15,00 = **29,70 €** (IPOTESI base). Con un tasso di utilizzo aggiuntivo del 5% (IPOTESI) il costo medio per ordine è ≈ **1,49 €**, più della contribuzione dello scenario base (**1,00 €**, doc 02): **non sostenibile nello scenario base**. È sostenibile solo in uno scenario con contribuzione ≥ ~10 € (lo scenario ottimistico del doc 02). Decisione: partire con i soli obblighi di legge comunicati bene; rivalutare la garanzia estesa dopo 100 ordini reali.

### 5.5 Punteggio sull'equazione del valore (1–10, prima → dopo lo stack)

| Elemento | Prima (prodotto "nudo" da trend) | Dopo lo stack | Cosa lo muove |
| --- | :-: | :-: | --- |
| Risultato desiderato | 5 | 6 | Bundle orientato al risultato |
| Probabilità percepita | 2 | 5 | Identità aziendale visibile, recensioni vere, foto reali, policy chiare |
| Tempo al risultato | 3 | 6 | Magazzino UE, tempi dichiarati, tracking |
| Sforzo/sacrificio | 5 | 7 | Guida in italiano, supporto, reso semplice |

Questi punteggi sono un giudizio qualitativo dell'agente, **non** un risultato misurato.

**Re-test non eseguito.** Passi previsti dal metodo, da fare dopo la scelta della nicchia: scrivere `pitch.md` (3–6 righe, nessun superlativo), eseguire `/founder-consumer --quick` (20 acquirenti simulati) con e senza stack, stesso seed, e confrontare obiezioni e tasso d'acquisto. Il tasso del panel va trattato come **limite superiore**: i buyer simulati tendono a essere accondiscendenti. Conferma reale con una landing con prezzo o una pre-vendita.

---

## 6. Pricing (metodo *founder-pricing*)

**Cosa manca:** la curva Van Westendorp (serve il panel o un sondaggio reale) e i prezzi dei concorrenti diretti (serve la nicchia). **Non è indicata nessuna "fascia accettabile"**: sarebbe inventata.

**Cosa si può già dire dai numeri** (strumento del CFO, scenario base, CPA e conversione tenuti fissi — semplificazione ottimistica, perché a prezzo più alto la conversione di solito cala e il CPA sale):

| Prezzo al pubblico IVA incl. (IPOTESI) | Netto IVA 22% | Contribuzione/ordine | Break-even (ordini/giorno) | Margine al piano (10/giorno) | Anno 1 operativo |
| --- | ---: | ---: | ---: | ---: | ---: |
| 34,90 € | 28,61 € | −3,09 € | mai | −17% | −13.379 € |
| **39,90 €** (base) | 32,70 € | 1,00 € | 19 | −3% | −4.422 € |
| 44,90 € | 36,80 € | 5,10 € | 4 | 9% | +4.557 € |
| 49,90 € | 40,90 € | 9,20 € | 2 | 18% | +13.536 € |

**Lettura:** con un costo sbarcato (prodotto + spedizione) di ~13,50 € (IPOTESI), sotto ~40 € IVA inclusa il modello a pagamento ads non sta in piedi. La regola operativa che ne deriva: **prezzo al pubblico ≥ ~3–3,5x il costo sbarcato**, oppure non vendere quel prodotto con ads a pagamento.

**Raccomandazione (da validare):**
1. **Prezzo:** scegliere prodotti/bundle che si possano vendere credibilmente a **44,90–49,90 € IVA incl.** con costo sbarcato ≤ 13,50 €. Il prezzo esatto dopo panel + verifica concorrenti.
2. **Scala (good/better/best):** 1 pezzo / kit da 2 (+ accessorio) / kit famiglia o ricarica. Ogni gradino aumenta lo scontrino senza aumentare il CPA (lo stesso clic compra di più).
3. **Offerta di lancio:** bonus (guida o accessorio) per i primi N ordini con data di fine dichiarata, **non** sconti sul prezzo (allenano ad aspettare e complicano la regola Omnibus sul prezzo precedente).
4. **Cosa testare con clienti veri:** due prezzi (es. 44,90 € vs 49,90 €) su due landing o due ad set, a parità di creatività; misurare conversione, CPA e ROAS vs break-even (doc 02 §4).
5. **Divieti:** nessun prezzo barrato "era 79,90 €" mai praticato; in caso di riduzione di prezzo va indicato il prezzo più basso dei 30 giorni precedenti (doc 03).

---

## 7. Business plan (metodo *founder-plan*)

### 7.1 Verdetto calcolato (da `compile.py --check` sui numeri del doc 02)

| Scenario | Verdetto calcolato | Perché |
| --- | --- | --- |
| Pessimo | **Not yet** | Ogni ordine perde 9,00 € prima dei costi fissi; anno 1 −14.172 € |
| Base | **Not yet** | Contribuzione +1,00 €/ordine ma anno 1 operativo −4.422 €; break-even 19 ordini/giorno |
| Ottimo | **Profitable** (sulle sole ipotesi) | Contribuzione 10,95 €/ordine; anno 1 +39.049 € **prima di imposte e senza remunerare il tempo del fondatore** |

Il controllo "panel consumatori" non è incluso perché il panel non è stato eseguito: il verdetto è quindi **parziale**. I numeri sono proiezioni su IPOTESI; solo preventivi reali e vendite reali li confermano.

### 7.2 Sintesi esecutiva

- **Cosa:** un brand e-commerce di micro-nicchia per il mercato italiano, rifornito in dropshipping da magazzino UE, con un'app interna che automatizza ricerca, schede, varianti creative e operazioni ripetitive.
- **Verdetto:** *Not yet* nello scenario base. Diventa sostenibile solo se si ottengono insieme scontrino ≥ ~45 € e CPA ≤ ~11–12 € (doc 02 §5).
- **La variabile che decide tutto:** il **CPA** (costo pubblicitario per ordine). Ogni euro di CPA in più è un euro di margine in meno.
- **Il rischio più grande:** blocco di account ads o pagamenti (ferma le vendite e la cassa). Mitigazione: compliance completa *prima* del lancio, due canali, riserva di cassa, lista email propria.
- **Cosa serve per partire:** 2.000 € (IPOTESI) di cui ~1.165 € spesi in setup e test e il resto come riserva; partita IVA attiva; 15–20 h/settimana.
- **La cosa da fare questa settimana:** scegliere 3 micro-nicchie candidate e, per ognuna, trovare 2 fornitori con magazzino UE e chiedere preventivo (prodotto + spedizione IT) e documentazione GPSR/CE.

### 7.3 Piano a 90 giorni con gate e criteri di stop

| Settimane | Obiettivo | Gate per proseguire |
| --- | --- | --- |
| 1–2 | Scelta nicchia (3 candidate → 1); preventivi fornitori UE; consulto commercialista su regime fiscale | Costo sbarcato ≤ 1/3 del prezzo target; fornitore con responsabile UE GPSR e documentazione |
| 3–4 | Partita IVA/SCIA, store, policy legali, cookie banner, campioni ricevuti e provati; panel `--quick` | Campione conforme alle foto; panel non boccia l'offerta |
| 5–8 | Test: 2–3 prodotti/angoli, budget ads ~25 €/giorno (IPOTESI), stop per prodotto a ~2x il CPA massimo senza vendite | Almeno un prodotto con ROAS ≥ break-even su ≥ 20 ordini |
| 9–12 | Ottimizzazione offerta/bundle; email post-acquisto; misura resi e dispute | ROAS sopra break-even su ≥ 50 ordini; tasso dispute sotto ~0,5% (IPOTESI di sicurezza) |

**Criteri di stop (decisi ora, prima di spendere):**
- perdita cumulata pari al **budget di test** (IPOTESI 1.000–1.200 €) senza alcun prodotto sopra break-even ROAS → fermarsi e rivalutare nicchia o modello;
- account ads o pagamenti sospesi due volte → fermarsi e rivedere compliance prima di riaprire;
- dispute/chargeback in crescita oltre ~1% → stop alle ads finché la causa non è risolta.

### 7.4 Versione una pagina (per un socio o un finanziatore)

- **Problema/cliente:** da definire con la nicchia (vincolo: dolore reale, acquisto ripetuto, pubblico raggiungibile in Italia).
- **Offerta e prezzo:** kit orientato al risultato, 44,90–49,90 € IVA incl. (IPOTESI da testare), consegna UE, supporto in italiano.
- **Numeri chiave (IPOTESI, doc 02):** contribuzione/ordine −9,00 € / +1,00 € / +10,95 € (pessimo/base/ottimo); break-even mai / 19 / 2 ordini al giorno; anno 1 operativo −14.172 € / −4.422 € / +39.049 €.
- **Evidenze:** nessuna ancora (nessun panel, nessuna vendita, nessun preventivo). Questo è il punto debole principale.
- **A cosa servono i soldi:** campioni, test ads su più prodotti, setup legale/fiscale, riserva di cassa per payout ritardati e rimborsi.
- **La richiesta:** nessuna richiesta di capitale esterno raccomandata prima di 50 ordini reali sopra break-even.
