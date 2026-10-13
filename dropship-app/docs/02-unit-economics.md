# 02 — Unit economics (metodo *founder-cfo*)

> **Leggere prima.** Tutti i valori di input sono **IPOTESI** dell'agente: nessuno
> viene da un preventivo, una fattura o un listino verificato in questa sessione.
> I risultati sono calcolati con `unit_economics.py` (pacchetto *founder-cfo*,
> eseguito con `python3 -I`) sulle ipotesi sotto: sono **corretti come aritmetica,
> non come previsione**. Lo strumento stampa il simbolo `$`; qui è sostituito da `€`
> perché tutti gli input sono in euro.
>
> Non è consulenza finanziaria, fiscale o legale: un commercialista deve verificare
> regime fiscale, contributi e IVA prima che si muova denaro.

---

## 1. L'unità e le convenzioni

- **Unità:** un ordine (un prodotto o un bundle spedito a un cliente).
- **Prezzo:** quello che lo strumento chiama `price` è il **ricavo netto IVA**. Il prezzo al pubblico (IVA inclusa, come lo vede il cliente) è diviso per 1,22 (IVA ordinaria italiana 22%). Esempio: 39,90 € → 32,70 €.
- **CPA** (costo per acquisizione) = spesa pubblicitaria ÷ ordini. È trattato come costo variabile per ordine.
- **Esclusi dal calcolo** (da tenere presenti): imposte sul reddito; **il tempo del fondatore, non remunerato**; costo del capitale; IVA su vendite in altri Paesi UE (vedi §7).
- **Giorni di vendita:** 30 al mese. **Capacità:** 40 ordini/giorno (IPOTESI: quanti ordini una persona può seguire tra supporto, resi e dispute).

---

## 2. Le ipotesi

### 2.1 Costi variabili per ordine

| Voce | Pessimo | Base | Ottimo | Natura e come verificarla |
| --- | ---: | ---: | ---: | --- |
| Prezzo al pubblico IVA incl. | 39,90 € | 39,90 € | 44,90 € (bundle) | IPOTESI → panel + test A/B (doc 01 §6) |
| Ricavo netto IVA (÷1,22) | 32,70 € | 32,70 € | 36,80 € | Calcolo |
| Prodotto (fornitore) | 9,00 € | 8,00 € | 7,50 € | IPOTESI → preventivo fornitore |
| Spedizione al cliente | 6,50 € | 5,50 € | 4,50 € | IPOTESI → preventivo fornitore/corriere da magazzino UE |
| Fee di pagamento | 1,20 € | 1,20 € | 1,35 € | IPOTESI (~3% del lordo, mix carte/PayPal) → listini pubblici del processore scelto; aggiungere l'eventuale commissione transazione della piattaforma se non si usa il suo gateway |
| CPA ads | 22,00 € | 15,00 € | 11,00 € | IPOTESI → **misurabile solo con test reali**; è la voce più incerta |
| Accantonamento resi/rimborsi/chargeback | 3,00 € | 2,00 € | 1,50 € | IPOTESI: base ≈ 6% degli ordini rimborsati con perdita media ~33 € (prodotto, spedizione, fee e CPA non recuperabili) |
| **Totale variabile** | **42,70 €** | **31,70 €** | **25,85 €** | Calcolo |
| **Contribuzione per ordine** | **−9,00 €** | **+1,00 €** | **+10,95 €** | Output strumento |
| Contribuzione % | −28% | 3% | 30% | Output strumento |

### 2.2 Costi fissi mensili (uguali nei tre scenari)

| Voce | €/mese | Nota |
| --- | ---: | --- |
| Piattaforma store (piano base) | 36 | IPOTESI → listino pubblico della piattaforma |
| App (import ordini, recensioni, upsell) | 40 | IPOTESI |
| Helpdesk + email marketing | 20 | IPOTESI (piani entry) |
| Privacy/cookie policy in abbonamento | 5 | IPOTESI |
| Commercialista | 60 | IPOTESI → chiedere preventivo |
| **Contributi INPS gestione commercianti (minimale)** | 370 | IPOTESI: ordine di grandezza del minimale annuo (~4.400–4.500 €) diviso 12; **da verificare** con il commercialista (importo aggiornato ogni anno, possibili riduzioni per forfettari, casi particolari se già dipendente) |
| Banca, dominio, varie | 20 | IPOTESI |
| **Totale** | **551** | |

Nota: l'INPS è il costo fisso più pesante. Se il commercialista conferma che non è dovuto (o è ridotto) nel caso specifico del fondatore, il break-even scende molto.

### 2.3 Spese di avvio (una tantum)

| Voce | € | Nota |
| --- | ---: | --- |
| Campioni prodotto | 150 | IPOTESI |
| Spesa ads su prodotti testati e scartati | 800 | IPOTESI: il costo dei test che non producono vendite sufficienti (oltre al CPA dei prodotti che vendono) |
| Apertura P.IVA + setup commercialista | 150 | IPOTESI |
| Setup legale/privacy | 50 | IPOTESI |
| Dominio + creatività di base | 15 | IPOTESI |
| **Totale** | **1.165** | |

Sul budget dichiarato di 2.000 € restano ~835 € come **riserva di cassa** (non inclusa nelle spese: serve per payout ritardati e rimborsi, §6).

### 2.4 Volumi (ordini/giorno, mesi 1→12)

| Scenario | Rampa | A regime |
| --- | --- | ---: |
| Pessimo | 0,5 · 1 · 1,5 · 2 · 2 · 3 · 3 · 3 · 3 · 3 · 3 · 3 | 3 |
| Base | 1 · 2 · 3 · 4 · 5 · 6 · 7 · 8 · 8 · 9 · 10 · 10 | 10 |
| Ottimo | 2 · 3 · 5 · 7 · 9 · 11 · 13 · 15 · 16 · 18 · 20 · 20 | 20 |

Tutte IPOTESI. Nessun panel né test reale è disponibile per calibrare la rampa: **la rampa è il punto dove i piani mentono di più**. Va sostituita con i dati delle prime 4–8 settimane di test.

---

## 3. Risultati per scenario (output dello strumento)

| | Pessimo | Base | Ottimo |
| --- | ---: | ---: | ---: |
| Contribuzione per ordine | −9,00 € | 1,00 € | 10,95 € |
| Break-even (ordini/giorno) | mai | 19 | 2 |
| Margine al volume di piano | −46% | −3% | 27% |
| Ricavi netti anno 1 | 27.468 € | 71.613 € | 153.456 € |
| **Risultato operativo anno 1** | **−14.172 €** | **−4.422 €** | **+39.049 €** |
| Dopo le spese di avvio | −15.337 € | −5.587 € | +37.884 € |
| Rientro della spesa di avvio | mai nell'anno 1 | mai nell'anno 1 | mese 3 |
| **Cassa necessaria** prima che si ripaghi | 15.337 € | 5.587 € | 1.165 € (+ capitale circolante, §6) |
| Verdetto `compile.py --check` | Not yet | Not yet | Profitable (solo sulle ipotesi) |

### 3.1 Cosa-se (stress test dello strumento)

| Scenario | Variazione | Margine al piano | Break-even/giorno | Anno 1 operativo |
| --- | --- | ---: | ---: | ---: |
| Base | — | −3% | 19 | −4.422 € |
| Base | prezzo −10% | −14% | mai | −11.583 € |
| Base | volume −20% | −4% | 19 | −4.860 € |
| Base | costi variabili +15% | −17% | mai | −14.835 € |
| Ottimo | — | 27% | 2 | +39.049 € |
| Ottimo | prezzo −10% | 19% | 3 | +23.704 € |
| Ottimo | volume −20% | 27% | 2 | +29.917 € |
| Ottimo | costi variabili +15% | 17% | 3 | +22.880 € |

### 3.2 Come leggere l'ottimo (senza farsi illudere)

Lo scenario ottimo richiede **contemporaneamente** scontrino 44,90 €, costo sbarcato 12 €, CPA 11 € (ROAS lordo ~4,1) e 20 ordini/giorno al mese 11. Ognuna di queste condizioni è possibile; tutte insieme e stabili per 12 mesi sono rare. Inoltre: il risultato è **prima delle imposte**, **non paga il tempo del fondatore**, e con ~153 k€ di ricavi supererebbe il limite di ricavi del regime forfettario (§7.3), cambiando il regime fiscale. Non va usato come previsione.

---

## 4. Break-even ROAS

**Definizioni.**
- ROAS = valore degli acquisti attribuiti ÷ spesa ads. Le piattaforme di solito riportano il valore **IVA inclusa** (quello del checkout): per questo si calcola il ROAS lordo.
- **CPA massimo** (contribuzione zero) = ricavo netto − costi variabili non pubblicitari.
- **Break-even ROAS (lordo)** = prezzo IVA incl. ÷ CPA massimo.

| | Pessimo | Base | Ottimo |
| --- | ---: | ---: | ---: |
| Costi variabili esclusa ads | 19,70 € | 16,70 € | 14,85 € |
| CPA massimo (contribuzione = 0) | 13,00 € | 16,00 € | 21,95 € |
| **Break-even ROAS lordo** | **3,07** | **2,49** | **2,05** |
| Break-even ROAS su netto IVA | 2,52 | 2,04 | 1,68 |
| ROAS ipotizzato (prezzo ÷ CPA) | 1,81 | 2,66 | 4,08 |

**ROAS per coprire anche i costi fissi** (base, a 10 ordini/giorno = 300/mese): costi fissi per ordine = 551 ÷ 300 = 1,84 € → CPA massimo 14,16 € → **ROAS lordo ≈ 2,82**.

Regola operativa per l'app: ogni prodotto/campagna ha un **ROAS soglia calcolato dai suoi costi reali**; sotto soglia dopo un budget di test predefinito → stop automatico proposto, conferma umana.

---

## 5. La leva che decide tutto: il CPA

Sensibilità dello scenario base al solo CPA (calcolo: contribuzione = 16,00 € − CPA; break-even = 551 € ÷ (contribuzione × 30), arrotondato per eccesso):

| CPA | ROAS lordo | Contribuzione/ordine | Break-even (ordini/giorno) |
| ---: | ---: | ---: | ---: |
| 10 € | 3,99 | 6,00 € | 4 |
| 12 € | 3,33 | 4,00 € | 5 |
| 15 € (base) | 2,66 | 1,00 € | 19 |
| 16 € | 2,49 | 0,00 € | mai |
| 18 € | 2,22 | −2,00 € | mai |

E al solo prezzo (CPA e conversione tenuti fissi, semplificazione ottimistica):

| Prezzo IVA incl. | Contribuzione/ordine | Break-even/giorno | Anno 1 operativo |
| ---: | ---: | ---: | ---: |
| 34,90 € | −3,09 € | mai | −13.379 € |
| 39,90 € | 1,00 € | 19 | −4.422 € |
| 44,90 € | 5,10 € | 4 | +4.557 € |
| 49,90 € | 9,20 € | 2 | +13.536 € |

**Tre modi di migliorare il margine (con il numero che muovono):**
1. **Scontrino medio** con bundle: da 39,90 € a 44,90 € la contribuzione passa da 1,00 € a 5,10 € (+4,10 €) a parità di CPA.
2. **CPA**: da 15 € a 12 € la contribuzione passa da 1,00 € a 4,00 € e il break-even da 19 a 5 ordini/giorno. Si muove con creatività, offerta e scelta del pubblico — non si "ordina".
3. **Costi fissi**: se l'INPS minimale non fosse dovuto o fosse ridotto (da verificare), i fissi scendono da 551 € a ~181 € (non dovuto) o ~421 € (riduzione del 35%, IPOTESI) al mese; a contribuzione 1,00 € il break-even resta comunque alto. **Lavorare sui fissi aiuta poco se la contribuzione è vicina a zero.**

---

## 6. Cassa: il problema nascosto

- **Scenario base:** la perdita cumulata supera i 2.000 € di budget **già nel mese 2** (−2.177 €). Con le ipotesi base, il budget non regge 12 mesi: la regola di stop del doc 01 §7.3 interviene prima.
- **Capitale circolante:** ads, fornitore e spedizione si pagano subito; gli incassi arrivano con ritardo (tempi di payout del processore; trattenute sui nuovi venditori; possibili riserve su account considerati a rischio). Esempio (IPOTESI): con payout a 7 giorni, a 10 ordini/giorno e 28,50 € pagati in anticipo per ordine (prodotto 8 + spedizione 5,50 + CPA 15), servono ≈ 7 × 10 × 28,50 = **~2.000 €** immobilizzati solo per sostenere quel volume. **Crescere consuma cassa**, anche quando ogni ordine è in utile.
- Con trattenute più lunghe (es. 21 giorni su una quota degli incassi) il fabbisogno si moltiplica.
- **Raccomandazione:** riserva di cassa separata (≥ 30% del budget, IPOTESI), tetto di spesa ads giornaliero legato alla cassa disponibile, non al ROAS.

---

## 7. IVA: OSS, IOSS, forfettario (impatto sui numeri)

> Questioni fiscali da far confermare al commercialista. Qui solo l'effetto sui conti.

### 7.1 Vendite ad altri Paesi UE (OSS)
- Sotto i **10.000 € annui** di vendite a distanza intra-UE (soglia complessiva UE) si applica l'IVA italiana; sopra, l'IVA del Paese del cliente, dichiarata e versata tramite lo sportello **OSS**.
- Con un prezzo unico IVA inclusa in tutta l'UE il netto cambia per Paese: 39,90 € → Germania (19%) 33,53 €; Francia (20%) 33,25 €; Spagna (21%) 32,98 €; Ungheria (27%) 31,42 €. Con contribuzione base di 1,00 €, vendere in Ungheria allo stesso prezzo porterebbe la contribuzione a −0,28 €. **I prezzi vanno fissati per Paese o con margine sufficiente.**

### 7.2 Merce spedita da fuori UE (IOSS)
- Per spedizioni di valore intrinseco ≤ 150 € importate e vendute a consumatori UE, lo sportello **IOSS** permette di incassare l'IVA al checkout e sdoganare senza costi a carico del cliente alla consegna. Senza IOSS il cliente può trovarsi a pagare IVA + diritti del corriere alla consegna → rifiuti del pacco, reclami, chargeback.
- Con fornitore a **magazzino UE** la merce è già importata: la vendita è domestica/intra-UE e questa complessità sparisce. Motivo in più per la raccomandazione del doc 01.

### 7.3 Variante: regime forfettario (IPOTESI fiscale da verificare)
In regime forfettario il venditore **non addebita IVA** sulle vendite in Italia, ma **non detrae** l'IVA sugli acquisti; inoltre, sui servizi acquistati da fornitori esteri (es. piattaforme pubblicitarie con sede in altro Paese UE) deve in genere integrare e versare l'IVA italiana senza poterla detrarre, il che rende la pubblicità ~22% più cara. Modellato così (IPOTESI): prezzo 39,90 € incassato per intero; prodotto e spedizione +22% (IVA all'importazione non detraibile); CPA +22%.

| Base in forfettario (IPOTESI) | Valore |
| --- | ---: |
| Contribuzione per ordine | 1,93 € (5%) |
| Break-even | 10 ordini/giorno |
| Margine al piano (10/giorno) | 0% |
| Anno 1 operativo | −2.385 € |
| Cassa necessaria | 3.606 € |

**Non incluse:** imposta sostitutiva (calcolata su ricavi × coefficiente di redditività del commercio, aliquota ridotta per i primi anni se ricorrono i requisiti) e contributi oltre il minimale. Limiti del regime: soglia di ricavi annua e compatibilità con OSS/IOSS **da verificare** con il commercialista. Il forfettario migliora un po' i conti a bassi volumi, ma non cambia la conclusione: con CPA 15 € e scontrino 39,90 € non si guadagna.

---

## 8. Nota del CFO (in parole semplici)

- **Il margine:** nello scenario base ogni ordine lascia **1,00 €** dopo ads e resi; al volume di piano il margine è **−3%**. Non è un business finché quel numero non sale.
- **La riga da guardare:** il **CPA**. Da 15 € a 18 € la contribuzione diventa −2,00 €; da 15 € a 12 € il break-even passa da 19 a 5 ordini al giorno (§5).
- **Cassa:** nello scenario base servono **5.587 €** prima che si ripaghi (non succede nell'anno 1); il budget di 2.000 € si esaurisce nel mese 2. A questo va aggiunto il capitale circolante per i payout ritardati (§6).
- **Tre leve:** scontrino (+4,10 € di contribuzione con bundle a 44,90 €), CPA (−3 € di CPA = +3 € di contribuzione), costi fissi (aiutano poco finché la contribuzione è vicina a zero).
- **Condizioni del board sul denaro** (doc 01 §2.4): "contribuzione positiva dopo CPA e resi con preventivi reali" → **non verificata** (nessun preventivo); "break-even ROAS calcolato" → **fatto** (§4); "ROAS reale misurato" → **da fare** con i test.
- Un commercialista deve verificare regime, contributi, IVA e struttura prima di aprire la partita IVA.

---

## 9. Riprodurre i calcoli

Gli input sono quelli delle tabelle §2. Per rieseguire (file `numbers.json` nel formato di `example.json` del pacchetto *founder-cfo*):

```bash
python3 -I <skill>/founder-cfo/unit_economics.py numbers.json --out cfo.md
python3 -I <skill>/founder-cfo/unit_economics.py numbers.json --price 36.80   # cosa-se prezzo (netto IVA)
python3 -I <skill>/founder-plan/compile.py --dir <cartella con numbers.json> --check
```

Quando arrivano preventivi e dati di test reali, sostituire le IPOTESI una per una, indicare la fonte accanto a ogni numero e rieseguire.

### Appendice — Anno 1 mese per mese (output strumento)

| Mese | Base: ordini/g | Base: risultato | Base: cumulato | Pessimo: cumulato | Ottimo: cumulato |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | −521 € | −1.686 € | −1.851 € | −1.059 € |
| 2 | 2 | −491 € | −2.177 € | −2.672 € | −625 € |
| 3 | 3 | −461 € | −2.638 € | −3.628 € | 467 € |
| 4 | 4 | −431 € | −3.069 € | −4.719 € | 2.215 € |
| 5 | 5 | −401 € | −3.470 € | −5.810 € | 4.621 € |
| 6 | 6 | −371 € | −3.841 € | −7.171 € | 7.683 € |
| 7 | 7 | −341 € | −4.182 € | −8.532 € | 11.403 € |
| 8 | 8 | −311 € | −4.493 € | −9.893 € | 15.779 € |
| 9 | 8 | −311 € | −4.804 € | −11.254 € | 20.484 € |
| 10 | 9 | −281 € | −5.085 € | −12.615 € | 25.846 € |
| 11 | 10 | −251 € | −5.336 € | −13.976 € | 31.865 € |
| 12 | 10 | −251 € | −5.587 € | −15.337 € | 37.884 € |

(I cumulati includono le spese di avvio di 1.165 €.)
