# Flussi email e SMS

Quattro flussi che l'app configura per ogni negozio: carrello abbandonato, post-acquisto con tracciamento, richiesta recensione, win-back. Prima dei flussi vengono i requisiti di consenso, perché decidono chi può ricevere cosa.

Questo documento riassume un orientamento prudente sulle regole italiane e UE (GDPR, art. 130 del Codice Privacy, Codice del Consumo). Non è un parere legale: va confermato da un consulente prima del primo lancio.

## 1. Consenso e GDPR

### 1.1 Tre tipi di messaggio

| Tipo | Esempi | Base giuridica | Serve il consenso marketing? |
|---|---|---|---|
| Transazionale | Conferma ordine, spedizione, tracciamento, ritardo, rimborso | Esecuzione del contratto | No. Il contenuto deve restare informativo: niente promozioni come parte principale. |
| Marketing a clienti (soft opt-in) | Prodotti analoghi a quelli acquistati, via email | Art. 130 c. 4 Codice Privacy | No, se l'email è stata raccolta durante l'acquisto, il cliente è stato informato e può opporsi in ogni messaggio. Solo email, solo prodotti analoghi. |
| Marketing | Carrello abbandonato di chi non ha mai comprato, newsletter, promozioni, win-back verso non clienti, tutti gli SMS promozionali | Consenso (art. 6.1.a GDPR, art. 130 Codice Privacy) | Sì, libero, specifico, informato, non preselezionato. |

Carrello abbandonato: chi abbandona il checkout non è ancora cliente, quindi il soft opt-in non si applica. Orientamento prudente: inviare il flusso solo a chi ha spuntato la casella di consenso marketing nel checkout. È una scelta che riduce il pubblico del flusso; l'alternativa va valutata con il consulente, non decisa dall'app.

Richiesta recensione: va trattata come marketing leggero. Inviarla a chi ha il consenso o rientra nel soft opt-in, sempre con il link per disiscriversi.

### 1.2 Raccolta del consenso

- Casella non preselezionata nel checkout e nei form di iscrizione, separata dall'accettazione dei termini di vendita.
- Testo della casella che dice cosa si riceve e con che frequenza indicativa. Esempio: "Voglio ricevere email su nuovi prodotti e promozioni del negozio, al massimo una a settimana. Posso disiscrivermi quando voglio."
- Consenso SMS separato da quello email, con il numero e la frequenza indicati.
- Double opt-in per newsletter e SMS: email o SMS di conferma prima di attivare l'invio. Rende il consenso dimostrabile.
- Nessun acquisto condizionato al consenso marketing.
- Nessun incentivo legato a una recensione positiva.

### 1.3 Registro dei consensi

Per ogni contatto l'app salva:

| Campo | Esempio |
|---|---|
| email / telefono | cliente@example.com |
| canale | email, sms |
| finalità | marketing, recensioni |
| fonte | checkout, popup, form footer |
| testo del consenso (versione) | v2026-10-01 |
| timestamp e fuso | 2026-10-20T21:14:03+02:00 |
| IP e user agent | per dimostrare il consenso |
| conferma double opt-in | timestamp |
| revoca | timestamp, canale della revoca |

### 1.4 Altri requisiti

- Link di disiscrizione in ogni email di marketing, attivo con un clic, e header `List-Unsubscribe` con disiscrizione one-click (richiesto da Gmail e Yahoo per chi invia volumi alti).
- SMS: istruzioni per la disiscrizione in ogni messaggio (es. "Rispondi STOP"), mittente identificabile, invio in orari diurni.
- Conservazione dei dati per finalità di marketing: definire un periodo nell'informativa. Il riferimento usato spesso in Italia è 24 mesi dall'ultimo contatto attivo, da confermare con il consulente.
- Informativa privacy che nomina il provider email/SMS come responsabile del trattamento, con DPA firmato e indicazione dei trasferimenti extra UE (Data Privacy Framework o clausole contrattuali standard).
- Autenticazione del dominio di invio: SPF, DKIM e DMARC configurati prima del primo invio.
- Liste di esclusione: chi ha revocato non rientra mai in un pubblico, neanche come lista caricata su Meta o TikTok.

## 2. Flusso carrello abbandonato

```
Nome flusso: Carrello abbandonato
Trigger: evento checkout_started con email, nessun ordine entro 1 ora
Condizione di ingresso: consenso_marketing_email == true
Obiettivo: completare l'ordine
Lunghezza: 3 email (+ 1 SMS opzionale solo con consenso SMS)
Uscita: ordine completato, disiscrizione, carrello svuotato, prodotto esaurito
Frequenza: un ingresso ogni 14 giorni per contatto
```

Email 1, dopo 1 ora: promemoria

- Oggetto: `La lampada a clip è ancora nel carrello`
- Anteprima: `Il carrello resta salvato. Se hai domande su consegna o reso, rispondi a questa email.`
- Testo:

> Ciao [nome],
>
> hai lasciato nel carrello la lampada da lettura a clip. L'abbiamo tenuta da parte.
>
> Se ti è venuto un dubbio su consegna, reso o funzionamento, rispondi a questa email e ti scriviamo noi.
>
> [Pulsante: Torna al carrello]
>
> [Firma con nome della persona che risponde]

Email 2, dopo 24 ore: obiezioni

- Oggetto: `Come funziona il reso, in breve`
- Anteprima: `Hai 14 giorni dalla consegna. Ecco i passaggi e chi paga la spedizione di ritorno.`
- Testo:

> Ciao [nome],
>
> le domande che riceviamo più spesso prima di un ordine riguardano consegna e reso, quindi eccole qui.
>
> Consegna: [N] giorni lavorativi in Italia, con numero di tracciamento via email.
> Reso: hai 14 giorni dalla consegna per restituire il prodotto. [Chi paga la spedizione di ritorno e quanto costa.]
> Pagamento: [metodi disponibili].
>
> [Pulsante: Completa l'ordine]

Email 3, dopo 72 ore: ultimo promemoria, senza pressione

- Oggetto: `Ti teniamo il carrello ancora per qualche giorno`
- Anteprima: `Dopo lo svuotiamo e non ti scriviamo più per questo ordine.`
- Testo:

> Ciao [nome],
>
> è l'ultima email su questo carrello. Fra qualche giorno lo svuotiamo.
>
> Se la lampada non fa per te, nessun problema. Se invece ti serve un'informazione per decidere, rispondi qui.
>
> [Pulsante: Vai al carrello]

Il flusso non usa sconti di default. Uno sconto nel carrello abbandonato insegna ai clienti ad abbandonare per ottenerlo. Se si vuole testare, si fa come esperimento con gruppo di controllo e si misura il margine, non solo il tasso di recupero.

SMS opzionale, dopo 4 ore (solo con consenso SMS, orario 9-20):

> [Negozio]: la lampada a clip è ancora nel tuo carrello: [link breve]. Rispondi STOP per non ricevere altri SMS.

## 3. Flusso post-acquisto con tracciamento

Questo flusso è transazionale. Nessuna promozione nel corpo principale; al massimo un riferimento discreto in fondo, solo per chi ha il consenso o il soft opt-in.

```
Nome flusso: Post-acquisto
Trigger: ordine pagato
Condizione di ingresso: nessuna (transazionale)
Obiettivo: informare, ridurre richieste "dov'è il mio ordine", ridurre rimborsi
Uscita: consegna confermata + 3 giorni, oppure rimborso
```

| # | Momento | Oggetto | Contenuto |
|---|---|---|---|
| 1 | Subito | `Ordine [numero] confermato` | Riepilogo, indirizzo, totale, tempi di consegna reali, come contattarci |
| 2 | Quando il fornitore comunica il tracciamento | `Il tuo ordine è partito` | Numero e link di tracciamento, corriere, data prevista |
| 3 | Se il tracciamento non si aggiorna da 5 giorni o la data prevista è superata | `Aggiornamento sulla consegna del tuo ordine` | Cosa sappiamo, nuova data stimata, possibilità di annullare se l'ordine non è ancora partito, contatto diretto |
| 4 | Consegna confermata | `Consegnato: due consigli per iniziare` | Prima ricarica, come si usa, link alla pagina resi |

Email 1, testo:

> Ciao [nome],
>
> abbiamo ricevuto il tuo ordine [numero].
>
> [Riepilogo prodotti e totale]
>
> La consegna è prevista in [N] giorni lavorativi. Quando il pacco parte ti mandiamo il numero di tracciamento.
>
> Per qualsiasi domanda rispondi a questa email.

Email 3 (ritardo), testo:

> Ciao [nome],
>
> il tuo ordine [numero] è in ritardo rispetto alla data che ti avevamo indicato. L'ultimo aggiornamento del corriere è del [data]: [stato].
>
> La nuova data stimata è il [data]. [Se l'ordine non è ancora partito: puoi annullarlo e ricevere il rimborso completo rispondendo a questa email.]
>
> Ci scusiamo per l'attesa.

L'email 3 è la più importante del flusso per un negozio dropshipping. Un ritardo comunicato prima che il cliente chieda riduce le contestazioni e i chargeback. Il trigger viene dal tracciamento, non da una data fissa.

Requisiti tecnici: l'app riceve il tracciamento dal fornitore via API o webhook; se il fornitore non lo fornisce entro 5 giorni dall'ordine, l'app apre un avviso interno.

## 4. Flusso richiesta recensione

```
Nome flusso: Richiesta recensione
Trigger: consegna confermata + 7 giorni (non dalla spedizione)
Condizione di ingresso: consenso_marketing_email == true OR soft_opt_in == true
Esclusioni: rimborso aperto, ticket di assistenza aperto, reso in corso
Lunghezza: 2 email
Uscita: recensione lasciata, disiscrizione
```

Email 1, consegna + 7 giorni

- Oggetto: `Com'è andata con la lampada a clip?`
- Anteprima: `Due minuti per dirci cosa funziona e cosa no. Pubblichiamo anche le recensioni negative.`
- Testo:

> Ciao [nome],
>
> la lampada è arrivata una settimana fa. Ci dici com'è andata?
>
> Pubblichiamo tutte le recensioni dei clienti che hanno comprato, anche quelle negative. Se qualcosa non va, rispondi a questa email e proviamo a sistemarlo.
>
> [Pulsante: Scrivi una recensione]

Email 2, consegna + 14 giorni, solo se non ha aperto o cliccato la prima

- Oggetto: `Ci dici com'è arrivata?`
- Anteprima: `La tua opinione ci serve per decidere se continuare a vendere questo prodotto.`

Regole:

- Si chiede la recensione a tutti i clienti idonei, non solo a chi sembra soddisfatto.
- Nessun incentivo legato al voto. Se si offre un incentivo per qualsiasi recensione, va dichiarato accanto alla recensione pubblicata.
- La pagina prodotto spiega come sono verificate le recensioni (solo acquirenti con ordine consegnato), come richiesto dalla direttiva Omnibus.
- Le recensioni con voto basso diventano un segnale per l'app: 3 recensioni sotto le 3 stelle sullo stesso difetto mettono in pausa le ads del prodotto e aprono una verifica sul fornitore.

## 5. Flusso win-back

Per prodotti d'impulso il riacquisto dello stesso prodotto è raro. Il win-back propone prodotti collegati o chiede se il cliente vuole ancora ricevere email.

```
Nome flusso: Win-back
Trigger: nessun ordine e nessun clic da 90 giorni dall'ultimo acquisto
Condizione di ingresso: consenso_marketing_email == true OR (soft_opt_in == true AND prodotto proposto analogo)
Lunghezza: 3 email in 21 giorni
Uscita: ordine, clic, disiscrizione; dopo l'ultima email senza risposta il contatto passa a "inattivo" e non riceve più marketing
```

| # | Momento | Oggetto | Contenuto |
|---|---|---|---|
| 1 | Giorno 0 | `Abbiamo aggiunto [nome prodotto]` | Un prodotto collegato a quello acquistato, con il motivo del collegamento |
| 2 | Giorno 10 | `Una guida per [uso del prodotto acquistato]` | Contenuto utile senza vendita: manutenzione, usi meno noti |
| 3 | Giorno 21 | `Vuoi ancora ricevere le nostre email?` | Un clic per restare, altrimenti smettiamo di scrivere |

Email 3, testo:

> Ciao [nome],
>
> non apri le nostre email da un po'. Va benissimo, ma non vogliamo riempirti la casella.
>
> Se vuoi continuare a riceverle, clicca qui sotto. Altrimenti non fare niente: da [data] smettiamo di scriverti.
>
> [Pulsante: Sì, continuate a scrivermi]

Pulire la lista così protegge la reputazione del dominio di invio, che con volumi piccoli si rovina facilmente.

## 6. Metriche dei flussi

| Flusso | Metrica principale | Metriche di controllo |
|---|---|---|
| Carrello abbandonato | Ricavo recuperato / carrelli entrati nel flusso | Disiscrizioni per invio, segnalazioni spam |
| Post-acquisto | Richieste "dov'è il mio ordine" per 100 ordini | Chargeback, rimborsi per ritardo |
| Recensioni | Recensioni ricevute / email inviate | Distribuzione dei voti, recensioni con difetto ricorrente |
| Win-back | Ordini da win-back / contatti entrati | Disiscrizioni, tasso di pulizia lista |

Le aperture sono poco affidabili (Apple Mail Privacy Protection le gonfia). Le decisioni si prendono su clic, ordini e disiscrizioni.

Soglie di allarme (IPOTESI): disiscrizioni oltre lo 0,5% per invio, segnalazioni spam oltre lo 0,1%. Sopra queste soglie l'app sospende il flusso e chiede una revisione.

## 7. Cosa resta manuale

- Testo del consenso e informativa: li scrive o li approva il consulente.
- Prima attivazione di ogni flusso e ogni modifica ai testi.
- Risposte alle email dei clienti su ritardi, rimborsi, reclami.
- Qualsiasi sconto inserito in un flusso.
