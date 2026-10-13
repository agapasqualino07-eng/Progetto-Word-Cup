# Brief per il board (autosufficiente)

## L'idea
Vedi sotto (copia di founder/idea.md):

# Dropship "problemi reali" (nome di lavoro; brand non ancora scelto)

- Cos'è: uno store online proprio (dropshipping) che vende prodotti fisici scelti dai dati: un software interno analizza discussioni online (YouTube, forum con RSS, Stack Exchange, Hacker News) per trovare problemi pratici ricorrenti, li incrocia con segnali di trend e margine, e propone prodotti che li risolvono. Store, schede e campagne sono generati in automatico, ma ogni pubblicazione/spesa richiede approvazione umana.
- Per chi: consumatori italiani (poi forse UE) con un problema pratico specifico (es. disordine cavi scrivania — esempio da dati MOCK, non reale).
- Cosa vende, a che prezzo: prodotti fisici da fornitori dropshipping con magazzino UE; ipotesi prezzo al pubblico 39,90–44,90 € IVA inclusa.
- Dove e come: online, Italia; clienti acquisiti con ads a pagamento (TikTok/Meta) + organico; consegna dal fornitore.
- Budget e vincoli: fondatore singolo, nessuna Partita IVA (vuole prima validare), budget ipotizzato ~2.000 € (NON confermato), ore settimanali NON note. Vuole "totalmente automatizzato".

## Cosa è già stato fatto (tutto in /home/user/Progetto-Word-Cup/dropship-app/)
- Software MVP (Python, 207 test verdi) che gira solo su dati MOCK: trend score, problem mining, guardrail (prodotti vietati, claim ingannevoli, approvazione umana, cap di spesa, kill switch), generazione store/campagne, inoltro ordini. Collegamenti reali non ancora testati.
- Template store, brand provvisorio, piano marketing, bozze legali.

## Numeri disponibili (TUTTI IPOTESI, nessun preventivo reale) — da docs/02-unit-economics.md
| | Pessimo | Base | Ottimo |
|---|---|---|---|
| Prezzo IVA incl. | 39,90 € | 39,90 € | 44,90 € |
| Costo prodotto | 9,00 | 8,00 | 7,50 |
| Spedizione | 6,50 | 5,50 | 4,50 |
| CPA ads | 22 | 15 | 11 |
| Contribuzione/ordine | −9,00 € | +1,00 € | +10,95 € |
| Risultato anno 1 | −14.172 € | −4.422 € | +39.049 € |
Costi fissi ~551 €/mese, di cui ~370 € INPS commercianti (da verificare). Nel caso base il budget finisce nel mese 2.

## Fatti di contesto (da ricerca web del 13/10/2026, fonti in docs/04, 05, 06)
- Competitor tool (AutoDS, Minea, Sell The Trend…) $20–50/mese; Shopify offre gratis generazione store/testi con AI.
- UE: dazio ~3 € su spedizioni extra-UE dal 1/7/2026; GPSR si applica al dropshipping; IVA OSS/IOSS.
- Fonti di discussione lecite coprono una minoranza delle conversazioni italiane (Facebook, TikTok, WhatsApp esclusi).
- Il "trend score" e il "problem score" hanno pesi non ancora calibrati su vendite reali.

## Piano proposto (Fase 0, pre-P.IVA, ~495 €)
Problem mining reale → 1–2 problemi → campioni da fornitori UE → landing con waitlist ("non ancora in vendita", nessun incasso) → piccolo test ads verso waitlist → se il costo per iscritto implica CPA ≤ ~11–12 €, aprire P.IVA e vendere.

## Domanda al board
Ha senso questa attività per questo fondatore, o è una perdita di tempo? Se ha senso, a quali condizioni e in quale forma più forte?
