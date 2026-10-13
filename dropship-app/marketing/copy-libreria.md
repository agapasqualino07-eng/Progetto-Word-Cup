# Libreria copy: hook, annunci, schede prodotto, oggetti email

Questa libreria alimenta il generatore di copy dell'app. Gli esempi usano il prodotto di ESEMPIO del file `campagne-template.json` (lampada da lettura a clip). I segnaposto tra parentesi quadre li riempie l'app con dati veri del prodotto. Se un dato manca, l'app scrive `DATO MANCANTE` e blocca la pubblicazione: non inventa numeri.

Tutti i testi rivolti al cliente sono passati con la skill humanizer: niente lineette lunghe, niente formule "non è X, è Y", niente chiusure a effetto, niente parole da brochure.

## 1. Regole che il generatore applica sempre

Il controllo automatico rifiuta un testo che contiene uno di questi elementi e lo manda a revisione umana.

Claim vietati o da verificare:

- "garantito", "garanzia" (salvo la garanzia legale, vedi nota sotto), "100%", "il migliore", "numero 1", "miracoloso", "rivoluzionario", "clinicamente testato" senza documento, "approvato da medici", "certificato" senza certificato allegato.
- Qualsiasi effetto sulla salute: dolore, sonno, ansia, postura, dimagrimento, pelle, capelli, vista. Anche in forma indiretta ("ti aiuta a dormire meglio").
- Prima/dopo su corpo, pelle, peso. Vietati in pratica su Meta e TikTok per molte categorie, e comunque fuorvianti con un prodotto da dropshipping.
- Attributi personali dello spettatore: "Hai mal di schiena?", "Sei stressata?", "Soffri d'insonnia?". Meta li vieta; usiamo la stessa regola anche su TikTok.
- Scarsità e urgenza non vere: "ultimi pezzi", "solo oggi", timer, "X persone lo stanno guardando". Ammessa solo una scadenza reale scritta con data e ora.
- Prezzi barrati e percentuali di sconto non conformi alla direttiva Omnibus (il riferimento è il prezzo più basso degli ultimi 30 giorni).
- Recensioni, citazioni o numeri di clienti che non vengono dal database ordini e recensioni verificate.
- Tempi di consegna diversi da quelli misurati. "Spedizione veloce" è vietato se la consegna supera 5 giorni lavorativi.
- Marchi altrui ("come quello di [marca]"), nomi di celebrità, "visto in TV".

Nota sulla garanzia: in UE il venditore deve per legge la garanzia di conformità di 24 mesi. Si può citare con le parole della legge ("garanzia legale di conformità di 24 mesi"), mai come promessa commerciale aggiuntiva.

Regole di stile (dalle skill copywriting, ad-creative e humanizer):

- Una frase, un fatto. Fatti specifici del prodotto battono gli aggettivi.
- Niente punti esclamativi, niente tutto maiuscolo, niente emoji usate come elenco puntato.
- Niente frasi fatte: "dì addio a", "porta X al livello successivo", "scopri il segreto", "rivoluziona", "il game changer".
- Niente coppie "non è solo X, è Y" e niente elenchi di negazioni ("niente fili, niente pile, niente stress").
- Test dello scambio: se la frase funziona uguale per il negozio di un concorrente, va riscritta con un dettaglio del prodotto.
- CTA che dice cosa succede: "Vedi i colori disponibili", "Ordina con reso entro 14 giorni".

## 2. Limiti di lunghezza

| Piattaforma | Elemento | Limite |
|---|---|---|
| Meta | Testo principale | 125 caratteri visibili prima del "Altro" |
| Meta | Titolo | circa 40 caratteri |
| Meta | Descrizione | circa 30 caratteri |
| TikTok | Testo annuncio | 100 caratteri massimo, consigliati 80 |
| TikTok/Reels | Testo a schermo | 2 righe, 3-5 parole per riga, dentro l'area sicura 9:16 |
| Google Shopping | Titolo prodotto nel feed | 150 caratteri; le prime 70 parole utili sono quelle che si vedono |
| Email | Oggetto | 40-60 caratteri |
| Email | Anteprima | 90-140 caratteri |

L'app conta i caratteri e propone una versione accorciata quando si supera il limite.

## 3. Angoli

Prima degli hook si scelgono 3-5 angoli, cioè motivi diversi per cui una persona dovrebbe fermarsi. Ogni angolo va collegato a una fonte: un commento reale, una domanda arrivata al servizio clienti, una caratteristica verificata sul campione.

| Angolo | Domanda che risponde | Esempio per il prodotto di ESEMPIO |
|---|---|---|
| Situazione quotidiana | In quale momento della giornata serve? | Leggere a letto mentre l'altra persona dorme |
| Dimostrazione | Come funziona, in pratica? | Si aggancia, si accende, si sceglie l'intensità |
| Obiezione | Cosa frena l'acquisto? | Tempi di consegna, durata della batteria, resi |
| Confronto onesto | Rispetto a cosa lo si sceglie? | Rispetto all'abat-jour: illumina solo la pagina |
| Identità | Per chi è? | Per chi legge in treno, in tenda, a letto |
| Regalo | A chi lo si regala? | A chi legge molto (solo nei periodi di regali, senza urgenza inventata) |

## 4. Framework di hook per video (TikTok e Reels)

Ogni hook ha tre parti che arrivano insieme nel primo secondo: l'immagine iniziale, la frase detta, il testo a schermo.

### 4.1 Situazione specifica

Schema: [momento preciso] + [fastidio concreto].

- "Leggo a letto e la luce del soffitto sveglia chi dorme accanto a me."
- "In treno la sera la luce sopra il sedile non arriva al libro."

### 4.2 Risultato mostrato subito

Schema: si mostra il risultato nel primo fotogramma, poi si spiega.

- Immagine: stanza buia, solo la pagina illuminata. Testo a schermo: "Luce sul libro, stanza al buio".

### 4.3 Risposta a un commento

Schema: screenshot del commento reale + risposta mostrata con il prodotto. Si usa solo con commenti veri e con il permesso implicito della piattaforma (commento pubblico sotto un nostro video).

- "Mi avete chiesto se si aggancia anche ai libri spessi. Questo ha 900 pagine."  (solo se provato davvero)

### 4.4 Tre passaggi

Schema: "[gesto 1], [gesto 2], [gesto 3]" con un taglio per gesto.

- "Aggancio, accendo, scelgo l'intensità."

### 4.5 Scoperta personale

Schema: chi parla racconta un'abitudine sua. Non presume nulla di chi guarda.

- "Da quando leggo con questa non accendo più la luce grande."  (solo se è vero per chi parla; nei video creator lo decide il creator)

### 4.6 Confronto onesto

Schema: oggetto che si usa di solito + limite concreto + alternativa.

- "L'abat-jour illumina mezza stanza. Questa solo la pagina."

### 4.7 Domanda nella voce del cliente

Schema: la domanda che il cliente si fa, detta con le sue parole. Non deve riguardare la sua salute o le sue condizioni personali.

- "Quanto dura la batteria? L'ho tenuta accesa una sera intera, ecco cosa resta."  (richiede misura reale)

Da evitare: "Fermati!", "POV:" generico, "Nessuno ti dice questo", "Questo cambierà la tua vita", "Ho trovato il prodotto più virale di TikTok".

## 5. Struttura degli annunci video

| Tempo | Parte | Cosa contiene |
|---|---|---|
| 0-3 s | Hook | Uno dei framework della sezione 4 |
| 3-8 s | Contesto | Il fastidio o la situazione, con immagini vere |
| 8-20 s | Prodotto in uso | Gesti reali, dettagli verificati, nessun effetto speciale che cambi l'aspetto del prodotto |
| 20-25 s | Informazioni d'acquisto | Prezzo, tempi di consegna reali, reso entro 14 giorni |
| 25-30 s | CTA | Cosa fare e cosa si ottiene |

Sottotitoli sempre, testo dentro l'area sicura, audio in licenza commerciale della piattaforma.

## 6. Testi per Meta e TikTok

### 6.1 Schema PAS breve (problema, conseguenza, soluzione)

Testo principale:
> La luce del soffitto sveglia chi dorme. Questa lampada si aggancia al libro e illumina solo la pagina. Ricarica USB-C, tre livelli di luce.

Titolo: `Lampada da lettura a clip`
Descrizione: `Reso entro 14 giorni`

### 6.2 Schema "fatti in fila"

Testo principale:
> Pesa [N] grammi, si aggancia a libri e testiere, si ricarica con il cavo del telefono. Arriva in [N] giorni lavorativi con tracciamento.

Titolo: `Si aggancia dove leggi`

### 6.3 Schema obiezione

Testo principale:
> Ci avete chiesto dei tempi di consegna. Dall'ordine all'arrivo in Italia passano [N] giorni lavorativi, con numero di tracciamento via email.

Titolo: `Spedizione tracciata in Italia`

### 6.4 Schema retargeting (messaggio diverso dall'annuncio originale)

Testo principale:
> Hai guardato la lampada a clip. Se il dubbio è il reso: hai 14 giorni dalla consegna e ti spieghiamo come fare in una pagina.

Titolo: `Come funziona il reso`

Questo testo cita una visita al sito. Va usato solo su pubblici di retargeting costruiti con il consenso cookie, e su Meta va riletto contro la policy sugli attributi personali: parla del prodotto visto, non della persona.

### 6.5 Testi TikTok (massimo 100 caratteri)

- `Luce sul libro, stanza al buio. Ricarica USB-C, tre livelli.`
- `Si aggancia al libro o alla testiera. Reso entro 14 giorni.`
- `Per leggere a letto senza accendere la luce grande.`

### 6.6 Promozione reale (solo se esiste)

> Fino a domenica [data] alle 23:59 la spedizione è gratuita su tutti gli ordini.

Requisiti: data e ora vere, promozione davvero attiva nel negozio, nessuna proroga automatica presentata come "ultima occasione".

## 7. Schede prodotto

Struttura che l'app genera. La pagina riprende le parole dell'annuncio vincente nel titolo e nel sottotitolo, così chi arriva dall'annuncio ritrova la stessa promessa.

1. Titolo: nome del prodotto chiaro, con la funzione principale.
2. Sottotitolo: l'hook dell'annuncio che ha portato il traffico, riscritto in una frase.
3. Prezzo, con prezzo barrato solo se conforme Omnibus.
4. Tempi di consegna reali e costo di spedizione, visibili prima del pulsante.
5. Pulsante d'acquisto.
6. Tre caratteristiche verificate, ognuna con il beneficio pratico.
7. Come si usa, in 3 passaggi con foto o GIF del prodotto reale.
8. Cosa c'è nella confezione.
9. Specifiche tecniche (misure, peso, materiali, batteria, certificazioni con documento).
10. Domande frequenti, prese da commenti e messaggi veri.
11. Reso e garanzia legale, in parole semplici.
12. Recensioni: sezione nascosta finché non ci sono recensioni verificate. Con la direttiva Omnibus va spiegato se e come le recensioni sono verificate.

### Esempio di scheda (prodotto di ESEMPIO)

> **Lampada da lettura a clip ricaricabile**
>
> Si aggancia al libro o alla testiera e illumina solo la pagina, così chi dorme accanto resta al buio.
>
> 34,90 €. Spedizione in [N] giorni lavorativi con tracciamento.
>
> **Caratteristiche**
> - Pinza imbottita: si aggancia a copertine e testiere fino a [N] cm senza segnarle.
> - Tre livelli di luce, si cambia con un tocco sul pulsante.
> - Si ricarica con un cavo USB-C, incluso nella confezione.
>
> **Come si usa**
> Aggancia la pinza, orienta il braccio flessibile, tieni premuto il pulsante per accendere.
>
> **Nella confezione**
> Lampada, cavo USB-C, istruzioni in italiano.
>
> **Reso**
> Hai 14 giorni dalla consegna per restituirla. Le istruzioni sono nella pagina Resi. Il prodotto ha la garanzia legale di conformità di 24 mesi.

Le misure, l'autonomia e i livelli di luce restano tra parentesi finché non sono verificati sul campione. La durata della batteria non compare finché qualcuno non l'ha misurata.

### Titolo per il feed Google Shopping

Schema: [tipo prodotto] + [caratteristica principale] + [variante] + [marca del negozio].

- `Lampada da lettura a clip ricaricabile USB-C, luce calda, nera`

## 8. Oggetti email

Regole: 40-60 caratteri, chiari prima che curiosi, niente "Re:" o "Fwd:" finti, niente urgenza inventata, niente emoji di default (si testano).

### Carrello abbandonato (solo con consenso, vedi `email-flussi.md`)

| Oggetto | Anteprima |
|---|---|
| La lampada a clip è ancora nel carrello | Il carrello resta salvato. Se hai domande su consegna o reso, rispondi a questa email. |
| Una domanda sulla tua lampada a clip | Se ti ha frenato qualcosa, scrivici: rispondiamo noi, non un sistema automatico. |
| Come funziona il reso, in breve | Hai 14 giorni dalla consegna. Ecco i passaggi e chi paga la spedizione di ritorno. |

### Ordine e spedizione (transazionali)

| Oggetto | Anteprima |
|---|---|
| Ordine [numero] confermato | Ecco il riepilogo. Ti scriviamo di nuovo quando parte, con il tracciamento. |
| Il tuo ordine è partito | Numero di tracciamento e data di consegna prevista dentro. |
| Aggiornamento sulla consegna del tuo ordine | La consegna è prevista per il [data]. Ti spieghiamo il motivo del ritardo. |
| Consegnato: due consigli per iniziare | Come caricarla la prima volta e come regolare la luce. |

### Richiesta recensione

| Oggetto | Anteprima |
|---|---|
| Com'è andata con la lampada a clip? | Due minuti per dirci cosa funziona e cosa no. Pubblichiamo anche le recensioni negative. |
| Ci dici com'è arrivata? | La tua opinione ci serve per decidere se continuare a vendere questo prodotto. |

### Win-back (solo clienti con consenso o soft opt-in)

| Oggetto | Anteprima |
|---|---|
| Abbiamo aggiunto [nome prodotto] | Pensato per chi ha già la lampada a clip. Ti mostriamo come si usano insieme. |
| Vuoi ancora ricevere le nostre email? | Se no, un clic e non ti scriviamo più. |

## 9. Testi per i creator (brief)

Il brief dice cosa mostrare e cosa non dire. Il copione lo scrive il creator.

- Mostra: il prodotto nel tuo uso reale, la ricarica, l'aggancio, la confezione arrivata a casa tua.
- Puoi dire: cosa ti piace e cosa no, quanto ci ha messo ad arrivare a te.
- Non dire: effetti sulla salute, "garantito", "il migliore", promesse sulla durata della batteria se non l'hai misurata, sconti non concordati.
- Obbligatorio: dicitura di pubblicità (#adv o "pubblicità") visibile all'inizio del contenuto, secondo le linee guida AGCOM e la Digital Chart IAP.
- Diritti: uso pubblicitario per [N] mesi, su quali piattaforme, compenso. Tutto per iscritto.

## 10. Checklist prima dell'approvazione

- [ ] Ogni dato numerico ha una fonte (campione misurato, scheda fornitore verificata, database ordini).
- [ ] Nessun claim sulla salute, nessun prima/dopo, nessun attributo personale.
- [ ] Tempi di consegna uguali a quelli della pagina spedizioni.
- [ ] Prezzo barrato e sconti conformi Omnibus, oppure assenti.
- [ ] Nessuna scarsità o urgenza non vera.
- [ ] Recensioni e citazioni solo da clienti verificati.
- [ ] Musica e immagini con licenza, nessun marchio altrui.
- [ ] Lunghezze entro i limiti della piattaforma.
- [ ] Letto ad alta voce: suona come una persona che parla.
