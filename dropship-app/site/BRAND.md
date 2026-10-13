# BRAND — app per store dropshipping (Italia/UE)

> Documento di lavoro dell'agente DESIGN. Nessun nome qui sotto è stato verificato
> come libero: sono **candidati**. Prima di usarne uno, completare i controlli
> della sezione 2. Questo non è un parere legale sui marchi.

## 0. Posizionamento (ipotesi da confermare con marketing)

- **Cosa fa:** individua prodotti in tendenza e genera in pochi minuti uno store
  pronto, già conforme alle regole UE per la vendita a distanza (resi 14 giorni,
  prezzi chiari, footer legale), da far rivedere a un professionista.
- **Per chi:** chi vuole vendere online in Italia/UE senza magazzino, spesso al
  primo progetto, che teme due cose: perdere soldi e "fare qualcosa di irregolare".
- **Promessa in una riga:** *Store veri, regole chiare, numeri onesti.*
- **Cosa NON siamo:** non "diventa ricco col dropshipping". Niente screenshot di
  fatturati, niente countdown, niente recensioni inventate — né nell'app né negli
  store che generiamo. È il nostro differenziale, non un limite.

## 1. Candidati nome

| # | Nome | Stile | Cosa dice | Come suona / si legge | Rischio |
|---|------|-------|-----------|-----------------------|---------|
| 1 | **Vetrinia** | inventato (da "vetrina") | il negozio che si mette in mostra | 4 sillabe morbide, facile da dettare; regge su icona 32px con la "V" | parola vicina a nomi esistenti di arredo/vetrine: alto rischio di omonimi |
| 2 | **Bottega Lampo** | evocativo, italiano | bottega = fiducia artigiana, lampo = velocità | lungo per un'icona; ok come wordmark, icona = fulmine stilizzato in "B" | "Lampo" è parola comune: debole come marchio da solo |
| 3 | **Trendaio** | descrittivo/inventato | chi lavora con le tendenze (come "fornaio") | simpatico, memorabile, italiano | assonanza con marketplace noti del settore moda (es. Trendyol): rischio confusione da valutare |
| 4 | Scaffale | descrittivo | lo spazio dove metti i prodotti | semplice | parola generica, non registrabile da sola |
| 5 | Negozio Pronto | descrittivo | lo store già fatto | chiarissimo | generico, debole come marchio |
| 6 | Banco | evocativo | il banco del mercato | breve | omonimie bancarie |
| 7 | Mercatino | evocativo | piccolo mercato | familiare | usato ovunque |
| 8 | Onda | evocativo | cavalcare l'onda della tendenza | breve | molto inflazionato |
| 9 | Vetra | inventato | vetrina + era | breve, internazionale | possibili omonimi industriali |
| 10 | Spuntino Shop | giocoso | piccolo, veloce | leggero | tono poco serio per chi teme di sbagliare |

**Shortlist: 1. Vetrinia · 2. Bottega Lampo · 3. Trendaio.**
Preferenza del design: **Vetrinia** (distintivo, funziona in italiano e in
inglese, si presta a un'icona semplice). Solo se supera i controlli.

## 2. Controlli da fare PRIMA di innamorarsi del nome

Posso eseguire solo ricerche pubbliche; la disponibilità del marchio la conferma
un consulente in proprietà industriale, e nulla è registrato finché non lo
registrate voi. **Stato di tutti e tre: NON VERIFICATO.**

| Controllo | Dove | Cosa cercare |
|-----------|------|--------------|
| Marchio UE | EUIPO eSearch plus — https://euipo.europa.eu/eSearch/ | nome identico e simile (anche fonetico) |
| Marchio in tutti gli uffici UE + nazionali | TMview — https://www.tmdn.org/tmview/ | idem, include UIBM e altri uffici nazionali |
| Marchio Italia | UIBM banca dati — https://uibm.mise.gov.it/ | idem |
| Classi di Nizza | 9 (software scaricabile/app), 35 (servizi di vendita al dettaglio online, pubblicità), 42 (SaaS, progettazione siti) | il conflitto conta soprattutto nelle stesse classi |
| Registro imprese | registroimprese.it | denominazioni sociali identiche |
| Dominio | registrar o whois (`whois vetrinia.it`, `.com`, `.eu`) | libero? se no, alternative: `getvetrinia.com`, `vetrinia.app`, `vetriniastore.it` |
| Handle | Instagram, TikTok, YouTube, X, Facebook | stesso handle disponibile ovunque, o variante coerente |
| Confusione | elenco competitor (da `marketing/`) + ricerca web | nessun nome/colore/logo vicino a un concorrente del settore |
| Lingue | significato in inglese, spagnolo, tedesco, francese | nessun significato negativo o ridicolo |

Esito: compilare la tabella "nome → esito di ciascun controllo → data → chi l'ha
fatto" e solo dopo depositare (UIBM o EUIPO, a seconda dei mercati).

## 3. Voce

Tre aggettivi, ognuno con un "sì" e un "no".

| Aggettivo | Sì | No |
|-----------|----|----|
| **Chiara** | "La spedizione arriva in 7–12 giorni lavorativi." | "Spedizione velocissima!!!" |
| **Onesta** | "Questo prodotto non ha ancora recensioni." | "Migliaia di clienti soddisfatti" (senza dati) |
| **Calma** | "Hai 14 giorni per ripensarci." | "Ultimi 3 pezzi! Affrettati!" (se non è vero e verificabile) |

**Prima / dopo** (riga tipica di uno store dropshipping):

- Prima: *"🔥 OFFERTA LIMITATA! -70% solo per oggi! Spedizione GRATIS e VELOCE!"*
- Dopo: *"€ 29,90 · Spedizione gratuita, consegna stimata 7–12 giorni lavorativi ·
  Reso entro 14 giorni."*

Regole di scrittura: frasi brevi, numeri precisi o nessun numero, seconda persona
singolare ("tu"), nessuna emoji come icona, maiuscolo solo per sigle.

**Tagline (3 opzioni):**
1. *Il tuo store, pronto e in regola.*
2. *Dalla tendenza al negozio, senza trucchi.*
3. *Vendi online con le carte in regola.*

## 4. Palette

Due livelli: il **brand dell'app** e il **tema di default degli store generati**
(personalizzabile per store via token `brand.*`, vedi `design-system.md`).

| Ruolo | Nome | Hex | Uso | Contrasto (WCAG 2.x) |
|-------|------|-----|-----|-----------------------|
| Primario | Pino | `#0F5E57` | brand, link, header, focus | bianco su Pino **7.61:1** (AAA) |
| Primario scuro | Pino notte | `#0B4A44` | hover/pressed | bianco **10.11:1** |
| Tinta primaria | Pino chiaro | `#E6F2F0` | badge informativi, sfondi box | Pino su tinta **6.64:1** |
| CTA | Terracotta | `#C2410C` | SOLO pulsante d'acquisto principale | bianco su Terracotta **5.18:1** (AA) |
| CTA scuro | Terracotta notte | `#9A3412` | hover CTA | bianco **7.31:1** |
| Testo | Inchiostro | `#1C1917` | testo principale | su bianco **17.49:1** |
| Testo secondario | Pietra | `#57534E` | descrizioni, note | su bianco **7.63:1**, su superficie **7.06:1** |
| Superficie | Carta | `#F7F6F3` | sezioni alterne, card | — |
| Bordo | Sabbia | `#E7E5E4` | bordi, divisori (non testo) | — |
| Successo | — | `#15803D` | "disponibile", conferme | su bianco **5.02:1** |
| Errore | — | `#B91C1C` | errori form | su bianco **6.47:1** |

Perché così: verde-pino comunica affidabilità e "in regola" senza il blu
generico dei SaaS; la terracotta è calda e italiana e rende il pulsante
d'acquisto l'unico elemento caldo della pagina (gerarchia CTA), **senza** il
rosso "allarme" tipico delle false urgenze. Nessun colore porta da solo
un'informazione (sempre testo o icona accanto).

## 5. Tipografia

| Ruolo | Font | Licenza | Dove |
|-------|------|---------|------|
| Titoli, prezzo | **Rubik** (500–700) | SIL Open Font License 1.1 | Google Fonts |
| Testo | **Nunito Sans** (400–700) | SIL Open Font License 1.1 | Google Fonts |
| Fallback | `system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif` | di sistema | — |

**Self-hosting obbligatorio**: i file `.woff2` sono in `template/assets/fonts/`.
Non caricare i font da `fonts.googleapis.com` negli store UE: il trasferimento
dell'IP del visitatore a Google senza consenso è stato ritenuto illecito
(LG München, 20/01/2022). Self-hosting = zero problema e pagina più veloce.

Scala: base 16px, rapporto ~1.2 (vedi token). Interlinea 1.5 per il testo,
1.2 per i titoli. Mai testo sotto 14px (note legali comprese: 14px).

## 6. Logo — brief

- Deve dire: negozio + affidabilità. Wordmark in Rubik 600 + simbolo semplice
  (per "Vetrinia": una "V" che forma il profilo di una tenda da bottega).
- Deve funzionare: favicon 32px e icona app 48px (solo simbolo), header store
  mobile alto 24px, monocromo su etichetta di spedizione, bianco su Pino.
- Evitare: carrelli della spesa, frecce di crescita/grafici (promessa di
  guadagno), fulmini aggressivi, gradienti, dettagli sotto 2px.
- Eventuali concept generati con strumenti di immagine sono **concept**, non un
  logo finito: va disegnato in vettoriale e verificato contro marchi esistenti.
- Negli store generati il logo è quello del **venditore** (`{{store_logo}}`) o,
  in mancanza, il nome dello store in Rubik: non mettiamo il nostro brand sugli
  store dei clienti se non in un discreto "Creato con …" opzionale.

## 7. I primi cinque punti di contatto

1. **Home dell'app**: titolo "Il tuo store, pronto e in regola", sotto: cosa fa
   in 3 passi, cosa NON promettiamo (niente guadagni garantiti), un'unica CTA.
2. **Store generato** (pagina prodotto): prezzo IVA inclusa, tempi di consegna
   reali, resi 14 giorni, contatti, P.IVA in footer — tutto visibile senza
   cercare. È il template in `template/product.html`.
3. **Email di conferma ordine** (dello store): riepilogo, data di consegna
   stimata come intervallo, link alla pagina resi, contatto umano.
4. **Primo post social dell'app**: un "prima/dopo" di uno store onesto vs uno
   pieno di finte urgenze — spiega il posizionamento meglio di uno slogan.
5. **Risposta al primo reclamo** (template per gli store): "Ci dispiace. Ecco
   cosa facciamo: [rimborso/sostituzione] entro [N] giorni. Il tuo diritto di
   recesso di 14 giorni resta valido." — mai scaricare la colpa sul fornitore:
   verso il cliente il venditore è lo store.
