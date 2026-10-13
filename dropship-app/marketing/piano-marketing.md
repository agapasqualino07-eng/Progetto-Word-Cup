# Piano marketing per i negozi generati dall'app

Ambito: negozi dropshipping in Italia e UE generati dall'app, con un budget iniziale di 1.000-3.000 € (IPOTESI, da confermare). Il piano dice quali canali usare, in che ordine spendere, quali numeri guardare e quali regole l'app può applicare da sola.

Premessa onesta. Il dropshipping con budget basso ha margini sottili e la maggior parte dei prodotti testati non regge la pubblicità a pagamento. Un test che fallisce è il caso normale, e il piano serve a farlo fallire spendendo poco. Nessuna cifra qui sotto è un risultato atteso: i numeri sono soglie di decisione, calcolate dall'economia del singolo prodotto.

## 1. Sintesi

- Si testa un prodotto alla volta, su una sola piattaforma a pagamento per volta, con un tetto di spesa per prodotto deciso prima di partire.
- Ogni regola di stop e di scaling deriva da un unico numero per prodotto: il CPA di pareggio (BE CPA). L'app lo calcola da prezzo, costo merce, spedizione, commissioni e resi stimati.
- L'app può fermare da sola ciò che perde soldi. Gli aumenti di budget restano proposte che una persona approva, almeno finché non esistono 4 settimane di dati puliti.
- Prima di spendere 1 € in ads servono tracciamento con consenso funzionante, pagine legali complete (recesso, spedizioni, privacy, cookie) e tempi di consegna dichiarati in modo veritiero.

## 2. Contesto e ipotesi

| Voce | Valore | Stato |
|---|---|---|
| Budget iniziale totale | 1.000-3.000 € | IPOTESI |
| Mercato | Italia, poi DE/FR/ES con negozi localizzati | IPOTESI |
| Tipo di prodotto | Fisico, prezzo 25-60 € IVA inclusa, acquisto d'impulso | IPOTESI |
| Tempi di consegna | Da fornitore reale; se superano 7 giorni lavorativi vanno scritti ovunque | DATO MANCANTE, dipende dal fornitore |
| Margine lordo | Da calcolare per prodotto | DATO MANCANTE |
| Team | Fondatore + app, nessun media buyer | IPOTESI |

Quadrante problema (dimensione × frequenza, dalla skill marketing-plan): i prodotti d'impulso risolvono di solito un problema piccolo e poco frequente. È il quadrante più debole. Conseguenze pratiche: il riacquisto è basso, l'email conta meno che in un e-commerce di marca, e la pubblicità deve rientrare sul primo ordine. Per questo il piano misura tutto sul primo acquisto e non conta su un LTV che oggi nessuno conosce.

## 3. Economia del prodotto: break-even ROAS e CPA

L'app calcola questi valori per ogni prodotto prima di creare una campagna. Senza questi numeri la campagna non parte.

```
prezzo_netto        = prezzo_ivato / (1 + aliquota_IVA)          # IT 22%
costi_variabili     = costo_merce + spedizione + commissione_pagamento
                      + accantonamento_resi_e_rimborsi + costo_app_per_ordine
contribuzione       = prezzo_netto - costi_variabili             # margine prima delle ads
BE_CPA              = contribuzione                               # CPA che porta a profitto zero
BE_ROAS             = prezzo_netto / contribuzione                # ROAS calcolato su ricavo netto IVA
target_CPA          = contribuzione - profitto_minimo_per_ordine
target_ROAS         = prezzo_netto / target_CPA
```

Esempio numerico (IPOTESI, prodotto di esempio):

| Voce | € |
|---|---|
| Prezzo IVA inclusa | 34,90 |
| Prezzo netto IVA 22% | 28,61 |
| Costo merce + spedizione fornitore | 11,00 |
| Commissione pagamento (circa 1,5% + 0,25) | 0,77 |
| Accantonamento resi/rimborsi (5% del netto) | 1,43 |
| Costo app/piattaforma per ordine | 0,50 |
| Contribuzione (= BE CPA) | 14,91 |
| BE ROAS | 1,92 |
| Profitto minimo voluto per ordine | 4,91 |
| Target CPA | 10,00 |
| Target ROAS | 2,86 |

Il BE CPA copre solo i costi variabili dell'ordine. I costi fissi mensili stimati in `docs/02-unit-economics.md` (circa 551 €/mese, IPOTESI, di cui la voce più pesante sono i contributi INPS) vanno coperti dal profitto per ordine moltiplicato per gli ordini del mese. Con lo scenario base di quel documento (prezzo 39,90 €, contribuzione prima delle ads 16,00 €, CPA ipotizzato 15,00 €) resta circa 1 € per ordine: servirebbero oltre 500 ordini al mese solo per pagare i fissi. Il target CPA va quindi fissato abbastanza sotto il BE CPA da lasciare un profitto reale, e il prodotto va scartato se non ci arriva.

Due regole che l'app applica:

1. Il valore di conversione inviato alle piattaforme è il subtotale prodotti IVA esclusa. Così il ROAS mostrato da Meta/TikTok/Google è confrontabile con il BE ROAS. Se si invia il lordo IVA, il ROAS di piattaforma risulta gonfiato del 22%.
2. Se il BE ROAS supera 3,0 il prodotto viene segnalato come "margine troppo basso per le ads" e non entra in test a pagamento. Può restare sul negozio per l'organico.

## 4. Canali

Il criterio di scelta viene dalle skill ads e founder-marketing: pochi canali, scelti in base a dove sta l'attenzione del cliente e a quanto costa un test leggibile.

| Canale | Ruolo | Quando | Costo indicativo | Come si capisce se funziona |
|---|---|---|---|---|
| TikTok Ads | Test creativi e primo acquisto su pubblico freddo | Fase 1, piattaforma A | Minimi di budget per gruppo annunci: verificare in Ads Manager al momento del lancio | Hook rate, CTR, CPA vs BE CPA |
| Meta Ads (FB/IG) | Test e scaling, retargeting | Fase 1 come piattaforma B, oppure A se il pubblico ha più di 35 anni | Nessun minimo rilevante | CPA vs BE CPA, frequenza |
| Google Shopping / PMax | Intercettare chi cerca già il prodotto | Fase 3, dopo almeno 30 acquisti tracciati | Serve Merchant Center approvato | ROAS su campagne non di marca |
| Organico TikTok / Reels | Test gratuito di hook e angoli, prova sociale reale | Da subito, sempre | Tempo (circa 1 h al giorno) | Retention a 3 secondi, condivisioni, salvataggi, commenti con domande d'acquisto |
| UGC / creator | Creatività credibili e Spark Ads / partnership ads | Fase 2, quando il prodotto ha già venduto | 50-200 € per video da micro-creator (IPOTESI) o prodotto in regalo | CPA dell'annuncio creator vs annunci del brand |
| Email / SMS | Recupero carrelli, post-acquisto, recensioni | Configurazione in Fase 0, attivi dal primo ordine | Piano gratuito o pochi € al mese fino a qualche migliaio di contatti | Ricavo da flussi, tasso di recupero carrelli |

Cosa non facciamo all'inizio e perché:

- Google Search su parole chiave generiche: CPC alti per prodotti d'impulso che la gente non cerca per nome.
- PMax dal giorno 1: senza storico di conversioni impara lentamente e con 20-30 €/giorno resta in apprendimento per settimane.
- Due piattaforme a pagamento insieme in Fase 1: con 1.000-3.000 € dividere il budget rende illeggibili entrambi i test.
- Influencer con fee alte, PR, affiliazione: rimandati a quando c'è un prodotto validato.

## 5. Sequenza di test e budget

Il budget si divide in quattro parti prima di partire. Esempio su 2.000 € (IPOTESI):

| Voce | Quota | Esempio su 2.000 € |
|---|---|---|
| Riserva non spendibile in ads (resi, chargeback, imprevisti fornitore) | 20% | 400 € |
| Campioni prodotto e creatività (ordini di prova, 1-2 creator) | 15% | 300 € |
| Test prodotti (Fase 1) | 45% | 900 € |
| Validazione e primo scaling (Fasi 2-3) | 20% | 400 € |

### Fase 0: preparazione (settimana 0, 0 € di ads)

- Ordinare il prodotto al fornitore e misurare i tempi reali di consegna in Italia.
- Girare 5-10 clip grezze con il prodotto vero (unboxing, uso, dettaglio). Senza prodotto fisico niente video: niente filmati presi da altri venditori.
- Pubblicare 1-2 video organici al giorno su TikTok e Reels con hook diversi. I due hook con retention migliore diventano i primi annunci.
- Tracciamento verificato con un ordine reale (vedi `tracking.md`), flussi email attivi (vedi `email-flussi.md`), pagine legali online.
- L'app calcola BE CPA, BE ROAS e target per ogni prodotto candidato.

### Fase 1: test creativi e prodotto (settimane 1-3)

- Un prodotto alla volta, 3-5 creatività con angoli diversi (vedi `copy-libreria.md`).
- Struttura: 1 campagna di conversione (evento Purchase; se in 3 giorni non arrivano conversioni, ottimizzare su AddToCart o InitiateCheckout come segnale temporaneo), 1 gruppo di annunci con pubblico ampio (Italia, 18+, nessun interesse), 3-5 annunci.
- Budget: 20-30 €/giorno per prodotto. Tetto per prodotto: il maggiore tra 150 € e 5 × BE CPA, ma mai oltre il 20% del budget test (con il prodotto di esempio: 150 €).
- Con 900 € di budget test si possono provare realisticamente 5-7 prodotti. Aspettarsi che 0-1 superino il test è ragionevole.

Criterio di uscita dalla Fase 1 (prodotto "promosso"): almeno 5 acquisti con CPA ≤ BE CPA sui dati degli ultimi 7 giorni, e almeno un annuncio con CTR sopra la mediana dell'account.

### Fase 2: validazione (settimane 3-5)

- Il prodotto promosso passa a 40-60 €/giorno.
- Si separano due campagne sullo stesso pubblico ampio (schema 80/20 della skill ads): una "scaling" con solo gli annunci provati (80% del budget) e una "test" con nuove varianti (20%).
- Si aggiungono 2-3 video UGC da creator e si provano come Spark Ads (TikTok) o partnership ads (Meta).
- Retargeting leggero (visitatori 7 giorni, carrelli 7 giorni) al 10-15% della spesa, con un messaggio diverso dall'annuncio originale: obiezione principale, spedizione e resi, uso pratico.

### Fase 3: scaling (dalla settimana 5)

- +20% di budget al massimo ogni 72 ore, mai +30% o più in un solo passo (azzera l'apprendimento).
- Si apre la seconda piattaforma a pagamento con gli stessi 2-3 annunci vincenti.
- Google Shopping/PMax solo dopo almeno 30 acquisti tracciati e feed approvato in Merchant Center.
- Lo scaling si giudica sul margine netto totale e sul MER complessivo, non sul ROAS del singolo gruppo di annunci.

## 6. Metriche

| Metrica | Formula | A cosa serve | Soglia di attenzione (IPOTESI, da tarare sui dati) |
|---|---|---|---|
| CPM | spesa / impressioni × 1000 | Costo dell'attenzione | +30% in 14 giorni: segnale precoce di fatica |
| Hook rate (video) | visualizzazioni 3 s / impressioni | Il primo secondo funziona? | Sotto il 25%: cambiare hook |
| CTR (link) | clic sul link / impressioni | L'annuncio genera interesse? | Sotto 0,8%: cambiare angolo o creatività |
| CPC (link) | spesa / clic sul link | Costo del traffico | Confronto tra annunci, non valore assoluto |
| Tasso aggiunta al carrello | ATC / sessioni pagina prodotto | La pagina prodotto convince? | Sotto 5%: problema di pagina o prezzo |
| CVR | acquisti / sessioni | Conversione del negozio | Sotto 1%: sistemare la pagina prima di spendere di più |
| CPA | spesa / acquisti | Costo per ordine | Confronto con BE CPA e target CPA |
| ROAS | ricavo netto IVA attribuito / spesa | Rendimento della piattaforma | Confronto con BE ROAS |
| BE ROAS | prezzo netto / contribuzione | Soglia di pareggio | Calcolato per prodotto |
| MER | ricavo netto totale / spesa ads totale | Verità a livello negozio | Sotto BE ROAS per 7 giorni: niente scaling |
| Frequenza | impressioni / copertura | Saturazione del pubblico | Freddo: oltre 2,5 attenzione, oltre 4 critico |
| Tasso rimborsi/resi | ordini rimborsati / ordini | Qualità reale del prodotto | Oltre 8%: sospendere le ads e verificare il fornitore |

Le soglie di CTR, hook rate e CVR sono punti di partenza da sostituire con le mediane dell'account dopo 30 giorni. La skill ads è esplicita: nessun benchmark esterno vale più dei propri dati.

## 7. Regole automatiche da implementare nell'app

Tutte le soglie sono multipli del BE CPA del prodotto, così le regole valgono per prodotti con prezzi diversi. Valutazione ogni 6 ore, decisioni su finestre di dati con attribuzione 7 giorni clic. Le regole che fermano possono girare in automatico. Le regole che aumentano la spesa producono una proposta da approvare.

### Protezioni globali (sempre attive, automatiche)

| ID | Condizione | Azione |
|---|---|---|
| G1 | Spesa del giorno sull'account ≥ cap giornaliero account | Mettere in pausa tutte le campagne fino a mezzanotte |
| G2 | Spesa cumulata del progetto ≥ budget totale - riserva | Pausa totale, notifica, nessuna ripartenza automatica |
| G3 | Spesa cumulata sul prodotto ≥ tetto prodotto | Pausa del prodotto |
| G4 | Evento Purchase assente da 24 h mentre la spesa supera 2 × BE CPA | Pausa e allarme "tracciamento rotto?" |
| G5 | Annuncio rifiutato o account limitato dalla piattaforma | Pausa campagne collegate, notifica, nessun reinvio automatico |
| G6 | Tasso rimborsi del prodotto > 8% su almeno 20 ordini | Pausa ads del prodotto, notifica |

### Stop-loss (automatici)

| ID | Livello | Condizione | Azione |
|---|---|---|---|
| S1 | Annuncio | Dopo 48 h, spesa < 30% della quota equa del gruppo | Pausa: la piattaforma lo ha già scartato |
| S2 | Annuncio | Spesa ≥ 1 × BE CPA, zero aggiunte al carrello, CTR sotto la mediana del gruppo | Pausa |
| S3 | Annuncio | Spesa ≥ 2 × BE CPA e zero acquisti | Pausa |
| S4 | Annuncio | Spesa ≥ 3 × BE CPA e CPA > 1,5 × BE CPA | Pausa |
| S5 | Prodotto | Spesa ≥ 3 × BE CPA sul prodotto e CPA del prodotto > 1,3 × BE CPA | Pausa prodotto, esito "test fallito" |
| S6 | Annuncio scaling | Frequenza > 3,5 oppure CTR -30% rispetto al picco dei 7 giorni migliori | Pausa e richiesta di nuova variante |

Regola di attesa: prima di S3-S5 servono almeno 72 ore dalla pubblicazione, perché gli acquisti arrivano con ritardo rispetto al clic. Nessuna regola modifica un annuncio attivo: si mette in pausa e se ne lancia uno nuovo, perché la modifica azzera l'apprendimento.

### Scaling (proposte da approvare)

| ID | Condizione | Proposta |
|---|---|---|
| U1 | CPA ≤ target CPA negli ultimi 3 giorni, almeno 10 acquisti in 7 giorni, frequenza < 2,5, MER 7 giorni ≥ BE ROAS | +20% budget, al massimo ogni 72 h |
| U2 | Dopo U1, CPA > 1,3 × target CPA per 2 giorni | -20% budget, pausa degli aumenti per 7 giorni |
| U3 | Annuncio in campagna test con almeno 5 acquisti, CPA ≤ target, attivo da 7 giorni | Spostarlo nella campagna scaling (nuova copia, l'originale resta) |
| U4 | Prodotto con almeno 30 acquisti tracciati | Proporre apertura Google Shopping/PMax |
| U5 | Annunci provati in scaling < 3 | Bloccare U1 e chiedere nuove creatività: non si scala il budget più in fretta delle creatività disponibili |

Dopo 4 settimane di dati puliti, U1 e U2 possono passare in automatico con un cap: nessun aumento automatico oltre il doppio del budget giornaliero approvato l'ultima volta da una persona.

## 8. Cosa non automatizzare

| Area | Perché resta manuale |
|---|---|
| Approvazione delle creatività | L'app genera bozze. Una persona controlla che il video mostri il prodotto reale, che i claim siano veri e che non ci siano diritti di terzi (musica, volti, marchi). |
| Claim e policy pubblicitarie | Salute, cosmetici, integratori, prima/dopo, attributi personali ("Hai mal di schiena?") e prezzi barrati hanno regole stringenti. L'app segnala; decide una persona. |
| Scelta di prodotti in categorie regolamentate | Integratori, dispositivi medici, cosmetici, giocattoli, elettronica con marcatura CE e prodotti soggetti al Regolamento UE sulla sicurezza generale dei prodotti (GPSR) richiedono verifiche su documenti e responsabile UE. |
| Sconti e prezzi barrati | Con la direttiva Omnibus il prezzo di riferimento di uno sconto è il prezzo più basso applicato nei 30 giorni precedenti. L'app calcola; una persona conferma. |
| Aumenti di budget nelle prime 4 settimane | Vedi sezione 7. |
| Contratti e brief con i creator | Diritti d'uso, durata, dicitura di pubblicità (#adv o "pubblicità") secondo le linee guida AGCOM e la Digital Chart IAP. |
| Risposte a commenti e messaggi su reclami, salute, ritardi | Rischio reputazionale e legale. L'app può proporre una bozza. |
| Ricorsi contro rifiuti o blocchi degli account pubblicitari | Ripetere in automatico un annuncio rifiutato peggiora la valutazione dell'account. |
| Pubblicazione dei post organici | L'app prepara bozze e calendario; la pubblicazione richiede un'approvazione esplicita. |

## 9. Lancio di ogni negozio

Adattato da launch e founder-launch: si parte con il test più economico, e la soglia di successo si scrive prima di vedere i dati.

| Giorno | Cosa | Responsabile |
|---|---|---|
| G-7 | Prodotto campione ricevuto, tempi di consegna misurati, foto e clip girate | Fondatore |
| G-6 | Pagine legali, recesso 14 giorni, spedizioni con tempi reali | App (bozza) + fondatore (verifica) |
| G-5 | Pixel, CAPI, GA4, consenso cookie testati con un ordine reale da 1 € o con il prodotto | Fondatore |
| G-5 → G-1 | 1-2 video organici al giorno, si annotano retention e commenti | Fondatore |
| G-2 | L'app genera 3-5 annunci dai due hook organici migliori; approvazione umana | App + fondatore |
| G-1 | Scritta la soglia di successo del test (es. "5 acquisti a CPA ≤ 14,91 € entro 150 € di spesa") | Fondatore |
| G0 | Campagna attiva a 20-30 €/giorno, regole G e S attive | App |
| G+3 | Prima lettura: consegna degli annunci, CTR, ATC. Nessuna decisione sugli acquisti | Fondatore |
| G+7 | Decisione: promosso, continua fino al tetto, oppure fermo | Fondatore con proposta dell'app |
| G+14 / G+30 | Revisione: MER, tasso rimborsi, recensioni reali, tempi di consegna effettivi | Fondatore |

Percorso critico: campione del prodotto e tracciamento. Se uno dei due slitta, slitta il lancio.

## 10. Organico e UGC

- Pilastri dei contenuti: prodotto in uso reale (50%), dietro le quinte del negozio e delle spedizioni (20%), domande dai commenti trasformate in video di risposta (20%), offerta (10%).
- Ogni video organico ha tre agganci nel primo secondo: immagine, frase detta, testo a schermo.
- I commenti di dubbio ("arriva davvero in Italia?", "quanto dura la batteria?") diventano annunci di tipo FAQ. È la fonte di angoli più utile e la meno usata.
- Creator: micro-creator italiani con pubblico in target, brief con cosa mostrare e cosa non dire, diritti d'uso pubblicitario per 3-6 mesi messi per iscritto, dicitura di pubblicità sempre presente.
- Recensioni: solo da clienti reali e verificati. Mai testi scritti dall'app o dal fondatore, mai recensioni importate da marketplace di altri venditori.

## 11. Esperimenti (A/B)

Con budget piccolo i test statistici classici sulle pagine non raggiungono quasi mai la numerosità necessaria (con CVR 2% servono migliaia di sessioni per variante). Quindi:

- Sugli annunci si testa l'angolo e l'hook, una variabile per volta, lasciando che la piattaforma distribuisca la spesa.
- Sulla pagina prodotto si cambia una cosa per volta in sequenza (prima/dopo) e si guarda il tasso di aggiunta al carrello su almeno 500 sessioni per versione, sapendo che è un segnale e non una prova statistica.
- Ogni test ha un'ipotesi scritta prima: "Poiché [osservazione], crediamo che [modifica] aumenterà [metrica] per [pubblico]. Lo verifichiamo con [metrica e soglia]."
- Registro dei test nell'app: ipotesi, varianti, spesa, risultato, decisione.

## 12. Leve psicologiche ammesse

Dalla skill marketing-psychology si usano solo leve che non ingannano:

| Leva | Uso consentito | Uso vietato nell'app |
|---|---|---|
| Riprova sociale | Numero reale di ordini o recensioni verificate, mostrato solo sopra una soglia minima | Contatori finti, "23 persone stanno guardando", recensioni inventate |
| Scarsità / urgenza | Fine reale di una promozione con data, scorte reali del fornitore | Timer che si azzerano, "ultimi 3 pezzi" falsi |
| Ancoraggio | Prezzo barrato solo se conforme a Omnibus | Prezzi di listino gonfiati per simulare sconti |
| Riduzione del rimpianto | Recesso 14 giorni spiegato in chiaro, costi di reso dichiarati | "Soddisfatti o rimborsati" se poi il reso costa più del prodotto |
| Facilità (Fogg, EAST) | Checkout corto, metodi di pagamento locali, costi di spedizione visibili subito | Costi aggiunti all'ultimo passaggio |
| Effetto Zeigarnik | Promemoria carrello con il consenso del cliente | Promemoria a chi non ha dato il consenso |
| Reciprocità | Guida d'uso gratuita del prodotto | Regali condizionati a una recensione positiva |

## 13. Decisioni aperte

1. Piattaforma del negozio (Shopify o motore proprietario): cambia l'integrazione di CAPI, del consenso e del feed prodotti.
2. Tempi di consegna reali dei fornitori scelti: DATO MANCANTE. Oltre 10 giorni lavorativi, conviene puntare su fornitori con magazzino UE prima di investire in ads.
3. Budget definitivo e quota di riserva.
4. Mercati UE successivi all'Italia: ognuno richiede lingua, pagine legali e servizio clienti locali.
5. Responsabile UE per la GPSR per i prodotti spediti da fuori UE.
6. Consulenza legale su privacy, consumatori e pubblicità prima del primo lancio. Questo documento non è un parere legale.
