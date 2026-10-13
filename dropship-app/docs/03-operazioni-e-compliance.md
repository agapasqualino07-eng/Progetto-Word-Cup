# 03 — Operazioni e compliance (metodo *founder-ops*)

> **Avvertenza.** Sintesi orientativa delle norme che di solito si applicano a un
> e-commerce in dropshipping con sede in Italia che vende a consumatori UE. Le
> regole cambiano e dipendono dal caso concreto (prodotto, regime fiscale, Paesi
> serviti). **Ogni punto va confermato con il commercialista, un legale o l'ente
> competente.** Non è consulenza legale o fiscale. I riferimenti normativi sono
> indicati per facilitare la verifica; dove l'agente non è certo del dettaglio è
> scritto **DA VERIFICARE**.

---

## 1. Il ciclo quotidiano di uno store in dropshipping

Legenda: **A** = automatizzabile · **A+U** = automatizzabile con approvazione umana · **U** = solo umano · 👁 = il cliente lo vede.

| # | Passo | 👁 | Automazione | Note |
| --- | --- | :-: | :-: | --- |
| 1 | Ordine ricevuto, pagamento autorizzato | 👁 | A | Controllo antifrode del processore; ordini sospetti in coda umana |
| 2 | Inoltro ordine al fornitore + pagamento fornitore | | A | Con regole: blocco se margine reale < soglia o fornitore senza stock |
| 3 | Conferma d'ordine con tempi di consegna onesti | 👁 | A | Template in italiano, tempi da dati reali del fornitore |
| 4 | Tracking caricato e inviato al cliente | 👁 | A | Allarme se il tracking non si aggiorna entro N giorni |
| 5 | Monitoraggio spedizioni in ritardo | 👁 | A+U | Email proattiva automatica; decisione su rimborso/rispedizione umana |
| 6 | Servizio clienti (domande, "dov'è il mio ordine") | 👁 | A+U | Bozza AI, invio automatico solo per FAQ a basso rischio |
| 7 | Resi, recessi, garanzia | 👁 | A+U | Moduli e istruzioni automatici; accettazione/rifiuto umano |
| 8 | Dispute e chargeback | | U (con raccolta prove A) | Le prove si raccolgono in automatico, la risposta la firma un umano |
| 9 | Campagne ads: lancio, budget, stop | | A+U | Regole di stop su ROAS soglia; nuove creatività e claim approvati da umano |
| 10 | Riconciliazione incassi/costi, contabilità | | A+U | Export automatico; registrazioni e dichiarazioni dal commercialista |
| 11 | Ricerca nuovi prodotti | | A+U | L'app propone; scelta, campioni e verifica conformità umani |

---

## 2. Cosa è automatizzabile e cosa NO

### 2.1 Automatizzabile (con buon rapporto beneficio/rischio)
- Raccolta segnali di tendenza e punteggio preliminare dei prodotti (input, non decisione).
- Calcolo automatico di prezzo minimo, CPA massimo e ROAS soglia per ogni prodotto (doc 02 §4).
- Bozze di schede prodotto, traduzioni, varianti di titolo/descrizione, varianti creative.
- Inoltro ordini, tracking, email transazionali, sequenze post-acquisto.
- Prima risposta alle FAQ (tempi, tracking, come fare un reso) con escalation.
- Regole di stop delle campagne sotto soglia (proposta automatica, esecuzione dopo conferma o entro limiti di budget pre-approvati).
- Raccolta delle prove per le dispute (tracking, conferme di consegna, comunicazioni).
- Report giornaliero: ordini, CPA, ROAS vs soglia, ritardi, ticket aperti, tasso dispute.

### 2.2 NON automatizzabile (o da non automatizzare)
- **Scelta finale del prodotto e verifica di sicurezza/conformità** (GPSR, marcatura CE, documentazione): responsabilità legale del venditore.
- **Approvazione di claim pubblicitari** (salute, prestazioni, "garantito", prima/dopo): rischio di pratiche commerciali scorrette e di ban.
- **Decisioni su rimborsi contestati, garanzia, recessi fuori standard.**
- **Risposte alle dispute/chargeback** e **appelli** per account ads o di pagamento sospesi.
- **KYC e verifiche identità** (Stripe, PayPal, piattaforme ads, Shopify): le fa il titolare, di persona.
- **Adempimenti fiscali** (dichiarazioni IVA/OSS, contabilità): commercialista.
- **Gestione di crisi**: richiamo di un prodotto, notifica di incidente di sicurezza, data breach.
- **Rapporto con i fornitori**: negoziazione, campioni, controllo qualità.

### 2.3 Punti dove serve un umano nel loop (checklist per l'app)

| Momento | Perché un umano | Cosa deve mostrare l'app |
| --- | --- | --- |
| Pubblicazione di un nuovo prodotto | Responsabilità GPSR/CE e garanzia | Scheda conformità compilata, documenti fornitore, foto dei campioni |
| Pubblicazione di una nuova inserzione | Claim e policy piattaforme | Testo, claim evidenziati, regole policy toccate |
| Aumento budget oltre soglia | Cassa | ROAS reale vs soglia, cassa disponibile, payout in sospeso |
| Rimborso sopra soglia (es. > 1 ordine o > 50 €) | Costi e frodi | Storico cliente, tracking, motivo |
| Risposta a disputa/chargeback | Rischio account pagamenti | Prove raccolte, scadenza |
| Ticket con parole chiave rischiose ("pericoloso", "si è bruciato", "avvocato", "allergia") | Possibile incidente di sicurezza | Ticket in testa alla coda, mai risposta automatica |
| Richieste privacy (accesso, cancellazione) | GDPR | Dati del cliente trovati nei sistemi |
| Qualunque sospensione di account | Appello | Cronologia e comunicazioni |

**Stima del tempo del fondatore (IPOTESI):** 15–20 h/settimana nei primi 3 mesi (setup, test, supporto); 8–12 h/settimana a regime a ~10 ordini/giorno, con picchi durante dispute o ban. Non è "passivo".

---

## 3. Fornitori (come scegliere e cosa chiedere)

Non sono stati raccolti preventivi in questa sessione. Categorie da valutare:
- **Grossisti/dropshipper con magazzino UE** (preferiti): consegna più rapida, merce già importata, più facile trovare un responsabile UE ai fini GPSR.
- **Agenti di sourcing in Cina con magazzino UE o spedizione con IOSS**: costi più bassi, tempi e compliance più difficili.
- **Marketplace all'ingrosso extra-UE senza stock UE**: sconsigliati per questo modello (tempi, dazi, conformità).

**Domande da fare a ogni fornitore (copiare nella richiesta di preventivo):**
1. Prezzo unitario e prezzo di spedizione verso l'Italia (e verso DE/FR/ES), tempi medi di consegna e corriere.
2. Magazzino di partenza (Paese) e disponibilità stock.
3. Nome e indirizzo del **fabbricante** e dell'**operatore economico responsabile nell'UE** (GPSR); etichettatura del prodotto.
4. Dichiarazione di conformità UE e marcatura CE (se applicabile), rapporti di prova, istruzioni e avvertenze in italiano.
5. Gestione dei resi difettosi: sostituzione, rimborso, entro quanto tempo (il venditore risponde comunque per 2 anni verso il cliente).
6. Spedizione "neutra" o con il proprio brand, inserto stampato, imballaggio.
7. Campione: costo e tempi.
8. Trattamento dei dati dei clienti (indirizzi) e Paese in cui sono trattati (GDPR, §6.4).

Quando arrivano i preventivi: aggiornare le IPOTESI del doc 02 §2 e rieseguire lo strumento del CFO.

---

## 4. Procedure operative (SOP)

### 4.1 Lancio di un nuovo prodotto
1. L'app propone il prodotto con punteggio e calcolo: prezzo minimo, CPA massimo, ROAS soglia.
2. Il fondatore verifica la **scheda conformità** (§6.2) e i documenti del fornitore. Manca qualcosa → stop.
3. Ordinare un campione; provarlo; scattare foto/video reali.
4. Approvare scheda e claim; pubblicare con tempi di consegna dichiarati.
5. Lanciare il test con budget massimo predefinito; stop proposto sotto soglia.

### 4.2 Reclamo o reso
1. Risposta entro 24 h lavorative (bozza AI ammessa, approvazione umana se non FAQ).
2. Recesso entro i 14 giorni: fornire istruzioni di reso; rimborsare **entro 14 giorni** dalla comunicazione di recesso (si può attendere il rientro del bene o la prova della spedizione).
3. Difetto (garanzia legale): riparazione/sostituzione o, se non possibile, riduzione prezzo/rimborso; il costo è del venditore, che poi si rivale sul fornitore se il contratto lo prevede.
4. Ticket con segnali di rischio sicurezza → §4.4.

### 4.3 Disputa/chargeback
1. Prima della disputa: se il cliente segnala un problema, risolvere subito (spesso un rimborso costa meno di una disputa persa più la commissione).
2. Disputa aperta: raccogliere prove (tracking con consegna, comunicazioni, policy accettate), rispondere entro la scadenza.
3. Monitorare il **tasso di dispute settimanale**; sopra la soglia interna (IPOTESI 0,5%) → pausa ads e analisi della causa.

### 4.4 Possibile incidente di sicurezza
1. Sospendere la vendita del prodotto.
2. Raccogliere i fatti; contattare il fornitore/fabbricante.
3. Valutare con un legale gli obblighi di notifica (il GPSR prevede la notifica degli incidenti tramite il portale UE dedicato, *Safety Business Gateway* — DA VERIFICARE i casi e i tempi).

### 4.5 Account ads o pagamenti sospeso
1. Non aprire account duplicati per aggirare il blocco (violazione dei termini, porta a ban permanenti).
2. Leggere la motivazione, correggere la causa (pagine policy, claim, dati aziendali), poi appello.
3. Nel frattempo: email ai clienti esistenti, canale di riserva già verificato.

---

## 5. Strumenti minimi

| Funzione | Esempio di soluzione | Nota |
| --- | --- | --- |
| Store e checkout | Piattaforma e-commerce hosted (es. Shopify) | Costo nel doc 02 §2.2 (IPOTESI) |
| Pagamenti | Gateway della piattaforma o Stripe + PayPal | KYC completo prima del lancio; un metodo di riserva |
| Import ordini/fornitore | App collegata al fornitore | Con regole di blocco su margine |
| Helpdesk + email | Helpdesk con inbox condivisa; email marketing con doppio consenso | Dati in UE se possibile |
| Privacy/cookie | Generatore di policy + banner conforme alle linee guida del Garante | |
| Contabilità | Export ordini/fee/rimborsi per il commercialista; fatturazione elettronica dove richiesta | |
| App interna (questo progetto) | Trend, calcoli, bozze, report, code di approvazione | Ogni azione rischiosa passa da una coda umana |

Prezzi dei prodotti software: da verificare sui listini pubblici al momento dell'attivazione.

---

## 6. Compliance

### 6.1 Aprire l'attività in Italia
- **Partita IVA** con codice ATECO del commercio al dettaglio via internet (**verificare il codice esatto nella classificazione ATECO 2025** in vigore). Vendere online in modo abituale è attività d'impresa: la "prestazione occasionale" non si applica.
- **Iscrizione al Registro delle Imprese** (Camera di Commercio) come ditta individuale, con **PEC**; **SCIA/comunicazione al SUAP** del Comune per il commercio elettronico (D.Lgs. 114/1998, art. 18 — DA VERIFICARE la modalità del proprio Comune).
- **INPS – Gestione commercianti**: contributi minimi dovuti anche senza utili (impatto nel doc 02 §2.2). Casi particolari (es. già lavoratore dipendente) da valutare con il commercialista.
- **Regime fiscale**: forfettario o ordinario. Effetti sull'IVA e sui costi delle ads nel doc 02 §7.3. Limite di ricavi del forfettario e compatibilità con OSS/IOSS **DA VERIFICARE**.
- **Informazioni obbligatorie sul sito** (D.Lgs. 70/2003 sul commercio elettronico e Codice del Consumo): denominazione, sede, P.IVA, contatti, numero REA/registro imprese, prezzi chiari IVA inclusa e costi di spedizione prima dell'ordine.
- Fonti: Agenzia delle Entrate, INPS, Registro Imprese / impresainungiorno.gov.it.

### 6.2 Diritti del consumatore (Codice del Consumo, D.Lgs. 206/2005)
- **Recesso 14 giorni** dalla consegna, senza motivazione (artt. 52 ss.). Se il venditore non informa correttamente, il termine si **allunga fino a 12 mesi**. Rimborso entro 14 giorni dal recesso (incluse le spese di consegna standard). Le spese di restituzione possono essere a carico del cliente **solo se** informato prima dell'acquisto.
- **Garanzia legale di conformità 2 anni** (artt. 128 ss., come modificati dal D.Lgs. 170/2021): risponde il **venditore**, cioè il dropshipper, non il fornitore. Per i difetti che si manifestano entro un anno dalla consegna si presume che esistessero già (DA VERIFICARE i dettagli applicativi). Non va presentata come "bonus".
- **Consegna**: entro 30 giorni salvo diverso accordo; i tempi vanno dichiarati prima dell'acquisto.
- **Prezzi e sconti (Direttiva Omnibus, art. 17-bis Codice del Consumo)**: in caso di riduzione di prezzo va indicato il **prezzo più basso applicato nei 30 giorni precedenti**. Niente prezzi barrati mai praticati.
- **Recensioni (Omnibus)**: indicare se e come si verifica che provengano da acquirenti reali; **vietato** pubblicare recensioni false o importare recensioni di altri venditori/marketplace come se fossero proprie.
- **Pratiche commerciali scorrette** (artt. 20 ss.): niente scarsità o countdown falsi, niente claim non dimostrabili. Vigilanza AGCM.
- **Risoluzione delle controversie online**: la piattaforma ODR UE è stata dismessa nel 2025 e il relativo obbligo di link è venuto meno (**DA VERIFICARE** lo stato attuale e se restano obblighi informativi su ADR).
- **Accessibilità (European Accessibility Act, in vigore dal 28 giugno 2025)**: le microimprese che forniscono servizi sono di norma esentate (DA VERIFICARE se si superano le soglie).

### 6.3 Sicurezza dei prodotti: GPSR (Reg. UE 2023/988, applicabile dal 13 dicembre 2024)
- Ogni prodotto di consumo venduto nell'UE deve essere **sicuro** e avere un **operatore economico responsabile stabilito nell'UE** (fabbricante, importatore, rappresentante autorizzato o fornitore di servizi di logistica). Un prodotto spedito da un fabbricante extra-UE senza responsabile UE **non va messo in vendita**.
- **Vendite a distanza (art. 19)**: la pagina prodotto deve mostrare in modo chiaro nome e indirizzo (anche elettronico) del fabbricante e, se extra-UE, del responsabile UE; informazioni per identificare il prodotto (immagine, tipo, lotto/modello); avvertenze e informazioni di sicurezza nella lingua del consumatore.
- Etichettatura sul prodotto/imballaggio con i dati del fabbricante e del responsabile UE.
- Obblighi di cooperazione con le autorità, gestione dei richiami e notifica degli incidenti (DA VERIFICARE caso per caso).
- **Normative di prodotto aggiuntive**, se applicabili: marcatura CE e dichiarazione di conformità (giocattoli, elettronica, apparecchiature radio, ecc.); **RAEE** (registrazione come produttore per apparecchiature elettriche vendute a distanza); **pile e batterie** (Reg. UE 2023/1542); **imballaggi** (etichettatura ambientale in Italia, CONAI; in altri Paesi UE registri EPR nazionali per imballaggi — es. Germania); cosmetici (persona responsabile e notifica CPNP); prodotti a contatto con alimenti. **Evitare all'inizio** categorie ad alta complessità: elettronica con batterie, giocattoli, cosmetici, integratori, dispositivi medici.

**Scheda conformità per prodotto (da compilare prima della pubblicazione):** categoria; normative applicabili; fabbricante e responsabile UE con indirizzi; dichiarazione di conformità / rapporti di prova; avvertenze e istruzioni in italiano; etichettatura verificata sul campione; obblighi EPR (RAEE/pile/imballaggi); esito controllo campione; firma del fondatore e data.

### 6.4 Privacy e cookie (GDPR, Reg. UE 2016/679; Codice Privacy; linee guida cookie del Garante, 2021)
- Informativa privacy, registro dei trattamenti (semplificato), basi giuridiche, tempi di conservazione.
- **Banner cookie**: rifiuto facile quanto l'accettazione (pulsante o "X" per chiudere senza consenso), nessun cookie wall, **nessun pixel di marketing** (Meta, TikTok, Google Ads) attivo prima del consenso. Anche gli invii lato server (es. API di conversione) richiedono una base giuridica valida — DA VERIFICARE con il legale.
- **Fornitori e trasferimenti extra-UE**: passare nome e indirizzo del cliente a un fornitore fuori dall'UE è un trasferimento di dati personali: servono accordo sul trattamento e garanzie (es. clausole contrattuali standard). Ulteriore motivo per preferire fornitori UE.
- **Email marketing**: consenso esplicito; eccezione del "soft opt-in" per clienti esistenti su prodotti analoghi con possibilità di opposizione (art. 130 c. 4 Codice Privacy).
- Diritti degli interessati: procedura per accesso/cancellazione entro i termini di legge.

### 6.5 IVA: OSS e IOSS
- **OSS**: oltre 10.000 € annui di vendite a distanza intra-UE si applica l'IVA del Paese del cliente, dichiarata trimestralmente tramite OSS (effetto sui prezzi nel doc 02 §7.1).
- **IOSS**: per beni importati di valore ≤ 150 € venduti a consumatori UE, consente di riscuotere l'IVA al checkout e sdoganare senza costi per il cliente. Senza IOSS: IVA e diritti del corriere alla consegna → pacchi rifiutati e dispute.
- Con fornitore a magazzino UE la questione import/IOSS si semplifica molto.
- Obblighi di registrazione, fatturazione e tenuta documentale: commercialista. Fonti: Agenzia delle Entrate; portale UE "VAT One Stop Shop".

### 6.6 Policy pubblicitarie (Meta, TikTok, Google)
Le piattaforme non vietano il dropshipping in quanto tale, ma sospendono spesso gli inserzionisti e-commerce per:
- **Esperienza cliente negativa**: Meta raccoglie il feedback degli acquirenti e può limitare o bloccare le inserzioni di chi ha un punteggio basso (tempi di consegna lunghi, prodotto diverso dalle foto, assistenza assente).
- **Pratiche commerciali inaccettabili / informazioni ingannevoli**: prezzi barrati falsi, scarsità falsa, claim non dimostrabili, "prima/dopo" su salute e corpo.
- **Google Merchant Center – "Misrepresentation"**: sospensioni frequenti per siti nuovi senza dati aziendali completi, contatti, policy di reso e spedizione chiare, o con offerte "troppo belle per essere vere".
- **Contenuti generati con AI**: avatar/testimonial sintetici presentati come clienti reali sono ingannevoli (pratiche scorrette) e violano le policy; dal 2 agosto 2026 si applicano anche gli obblighi di trasparenza dell'AI Act (Reg. UE 2024/1689, art. 50) per alcuni contenuti sintetici — DA VERIFICARE l'applicazione concreta alle creatività pubblicitarie.
- **Categorie con restrizioni**: salute/integratori, cosmetici con claim, prodotti per adulti, armi/coltelli, dispositivi medici, prodotti finanziari.
- Pratica: account business verificato, dominio verificato, crescita graduale della spesa, nessun account multiplo per aggirare blocchi, revisione umana di ogni inserzione nuova.

### 6.7 Pagamenti: KYC, riserve, chargeback (Stripe, PayPal, gateway della piattaforma)
- **KYC**: identità del titolare, dati della ditta, conto bancario intestato, descrizione dell'attività e dei prodotti coerente con lo store. Incoerenze → blocco dei payout.
- **Attività ad alto rischio**: i processori pubblicano elenchi di attività vietate o soggette a restrizioni; alcuni modelli (spedizione lunga, prodotti "trend", pre-ordini) possono portare a **riserve sui fondi** o chiusura — verificare l'elenco del processore rispetto alla nicchia scelta.
- **Trattenute sui nuovi venditori**: comuni nei primi mesi (es. fondi trattenuti fino alla consegna o per un periodo fisso) — impatto di cassa nel doc 02 §6.
- **Chargeback**: commissione per disputa (IPOTESI 15–20 €, da verificare sul listino) oltre al rimborso; i circuiti carte hanno programmi di monitoraggio per i commercianti con tassi di dispute elevati (soglie nell'ordine dell'1% — DA VERIFICARE). Superarli porta a penali, riserve o chiusura.
- **Descrittore di addebito** chiaro (il nome che il cliente vede sull'estratto conto) riduce le dispute "non riconosco l'addebito".

---

## 7. Registro dei rischi

| # | Rischio | Probabilità | Gravità | Piano |
| --- | --- | :-: | :-: | --- |
| 1 | Account ads sospeso | Alta | Alta | Compliance pre-lancio, appello documentato, canale di riserva, lista email |
| 2 | Processore di pagamento trattiene fondi o chiude l'account | Media | Molto alta | KYC completo, metodo di riserva, riserva di cassa, tasso dispute basso |
| 3 | CPA sopra il massimo (doc 02 §4) | Alta | Alta | Stop automatico proposto sotto ROAS soglia; budget di test limitato |
| 4 | Fornitore in ritardo / senza stock | Media | Alta | Secondo fornitore qualificato; avviso proattivo al cliente; regola di blocco vendite |
| 5 | Prodotto non conforme o pericoloso | Bassa-media | Molto alta | Scheda conformità, campioni, categorie a basso rischio, SOP §4.4 |
| 6 | Ondata di resi/garanzie | Media | Media | Foto reali, descrizioni oneste, accantonamento nel doc 02 |
| 7 | Copia dello store da concorrenti / saturazione | Alta | Media | Brand, bundle, servizio, lista clienti propria |
| 8 | Fondatore indisponibile (malattia, lavoro) | Media | Media | Risposte automatiche FAQ, pausa ads automatica se la coda umana supera N ticket |
| 9 | Errore fiscale (IVA/OSS, regime) | Media | Alta | Commercialista dall'inizio; verifiche trimestrali |
| 10 | Violazione privacy (pixel senza consenso, data breach) | Media | Media-alta | Banner conforme, accesso minimo ai dati, procedura breach (notifica al Garante entro 72 h quando dovuta) |

---

## 8. Checklist "pronto al lancio"

- [ ] Partita IVA, Registro Imprese, PEC, SCIA/SUAP, INPS — confermati dal commercialista
- [ ] Regime fiscale scelto e impatto IVA/ads ricalcolato (doc 02 §7)
- [ ] Pagine: chi siamo con dati aziendali, condizioni di vendita, recesso e resi, garanzia legale, spedizioni con tempi reali, privacy, cookie
- [ ] Banner cookie conforme; pixel bloccati senza consenso
- [ ] KYC completato su processore principale e di riserva
- [ ] Scheda conformità GPSR compilata e firmata per ogni prodotto; campioni provati
- [ ] Account ads business verificato; inserzioni riviste da un umano
- [ ] ROAS soglia calcolato per ogni prodotto con costi reali; regole di stop impostate
- [ ] Riserva di cassa separata (doc 02 §6)
- [ ] Code di approvazione umana attive nell'app (§2.3)
