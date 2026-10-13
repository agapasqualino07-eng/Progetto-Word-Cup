# Tracciamento, pixel, CAPI e attribuzione

Setup di misura per i negozi generati dall'app, compatibile con il consenso cookie richiesto in UE. Vale per qualunque motore di negozio; dove serve, ci sono note per Shopify.

Principio guida, dalla skill analytics: si traccia solo ciò che serve a prendere una decisione. Le decisioni del piano marketing sono poche (fermare, continuare, scalare un annuncio o un prodotto), quindi anche gli eventi sono pochi.

Non è un parere legale. Configurazione del banner cookie e informativa vanno verificate da un consulente.

## 1. Architettura

```
Browser (negozio)
  ├─ CMP (banner cookie, IAB TCF 2.2, certificata Google)
  │    └─ decide quali tag partono
  ├─ GTM web container
  │    ├─ GA4                (con Consent Mode v2)
  │    ├─ Google Ads tag     (con Consent Mode v2, Enhanced Conversions)
  │    ├─ Meta Pixel         (solo con consenso marketing)
  │    └─ TikTok Pixel       (solo con consenso marketing)
  └─ dataLayer con event_id univoco per ogni evento

Backend dell'app (fonte di verità sugli ordini)
  ├─ Meta Conversions API   (stesso event_id del pixel, solo se consenso marketing)
  ├─ TikTok Events API      (stesso event_id del pixel, solo se consenso marketing)
  ├─ Google Ads: conversioni avanzate / caricamento conversioni (solo se consenso)
  └─ Database ordini: ordini, rimborsi, fonte UTM, risposta "come ci hai conosciuto"
```

La fonte di verità sul numero di ordini e sul ricavo è il database dell'app. Le piattaforme spiegano da dove vengono gli ordini, ma non decidono quanti sono.

## 2. Consenso cookie (UE)

### 2.1 Banner

- Pulsanti "Accetta" e "Rifiuta" allo stesso livello e con la stessa evidenza (linee guida cookie del Garante, 2021).
- Categorie: necessari (sempre attivi), statistiche, marketing. Nessuna casella preselezionata.
- Chiudere il banner con la X equivale a rifiutare.
- Link alla cookie policy e possibilità di cambiare scelta in ogni momento (icona o link nel footer).
- Registro delle scelte con timestamp e versione del banner.
- CMP certificata Google e compatibile IAB TCF 2.2 (necessaria per Consent Mode v2 e per gli annunci Google nel SEE).

### 2.2 Consent Mode v2 (Google)

Stato di default prima della scelta dell'utente:

```javascript
gtag('consent', 'default', {
  'ad_storage': 'denied',
  'ad_user_data': 'denied',
  'ad_personalization': 'denied',
  'analytics_storage': 'denied',
  'functionality_storage': 'granted',
  'security_storage': 'granted',
  'wait_for_update': 500
});
```

Aggiornamento dopo la scelta (lo fa la CMP):

```javascript
gtag('consent', 'update', {
  'analytics_storage': 'granted',        // se accetta "statistiche"
  'ad_storage': 'granted',               // se accetta "marketing"
  'ad_user_data': 'granted',
  'ad_personalization': 'granted'
});
```

Scelta da prendere con il consulente: Consent Mode "base" (i tag Google non partono affatto senza consenso) oppure "avanzato" (i tag inviano ping senza cookie e Google modella le conversioni). Il default prudente per l'app è la modalità base.

### 2.3 Meta e TikTok

- I pixel si caricano solo dopo il consenso marketing. In alternativa, con Meta: `fbq('consent', 'revoke')` prima di `init` e `fbq('consent', 'grant')` dopo il consenso.
- CAPI e Events API dal server partono solo per eventi di utenti con consenso marketing. Il flag di consenso viaggia con l'ordine dal browser al backend.
- Senza consenso, l'ordine resta nel database dell'app e conta nel MER, ma non viene inviato alle piattaforme pubblicitarie.

Conseguenza da accettare: le piattaforme vedranno solo una parte degli acquisti reali. Per questo le decisioni di scaling guardano anche il MER calcolato sul database (vedi sezione 6).

## 3. Eventi

### 3.1 Piano eventi

| Evento GA4 | Meta | TikTok | Quando parte | Parametri |
|---|---|---|---|---|
| `page_view` | `PageView` | `Pageview` (automatico) | Ogni pagina | automatici |
| `view_item` | `ViewContent` | `ViewContent` | Pagina prodotto | item_id, item_name, price, currency |
| `add_to_cart` | `AddToCart` | `AddToCart` | Clic su "Aggiungi al carrello" riuscito | item_id, quantity, value, currency |
| `begin_checkout` | `InitiateCheckout` | `InitiateCheckout` | Ingresso nel checkout | value, currency, num_items |
| `add_shipping_info` | (non inviato) | (non inviato) | Indirizzo inserito | shipping_tier |
| `add_payment_info` | `AddPaymentInfo` | `AddPaymentInfo` | Metodo di pagamento scelto | payment_type |
| `purchase` | `Purchase` | `CompletePayment` | Pagamento confermato dal backend | transaction_id, value, currency, items |
| `refund` | (non inviato) | (non inviato) | Rimborso registrato | transaction_id, value |

Nomi in GA4: si usano gli eventi consigliati da Google con i loro nomi esatti, così i report e-commerce si popolano da soli.

Nomi su TikTok: verificare i nomi standard degli eventi nella documentazione attuale di TikTok Events API al momento dell'integrazione; quelli in tabella vanno confermati.

### 3.2 Valore delle conversioni

- `value` = subtotale prodotti IVA esclusa, senza spedizione. È lo stesso valore usato per il BE ROAS nel piano marketing.
- `currency` = `EUR` (o la valuta del negozio locale).
- `transaction_id` = ID ordine dell'app, identico su tutte le piattaforme.

### 3.3 Deduplicazione pixel + server

Ogni evento ha un `event_id` generato nel browser e salvato con l'ordine. Pixel e server inviano lo stesso `event_id` e lo stesso nome evento; Meta e TikTok scartano il duplicato.

```javascript
const eventId = crypto.randomUUID();
dataLayer.push({
  event: 'purchase',
  event_id: eventId,
  ecommerce: {
    transaction_id: 'ORD-10234',
    value: 28.61,
    currency: 'EUR',
    items: [{ item_id: 'PRD-ESEMPIO-001', item_name: 'Lampada da lettura a clip', price: 28.61, quantity: 1 }]
  }
});
```

Payload server Meta (schema, valori di esempio):

```json
{
  "event_name": "Purchase",
  "event_time": 1760990043,
  "event_id": "8a1c...-uuid",
  "action_source": "website",
  "event_source_url": "https://negozio-esempio.example/checkout/grazie",
  "user_data": {
    "em": ["<sha256 email normalizzata>"],
    "ph": ["<sha256 telefono E.164>"],
    "client_ip_address": "<ip>",
    "client_user_agent": "<ua>",
    "fbp": "<cookie _fbp>",
    "fbc": "<cookie _fbc se presente>"
  },
  "custom_data": { "currency": "EUR", "value": 28.61, "order_id": "ORD-10234" }
}
```

Regole:

- Email e telefono si normalizzano (minuscole, spazi rimossi, telefono con prefisso internazionale) e si inviano solo come hash SHA-256.
- Si invia solo se `consenso_marketing == true` per quella sessione.
- Nessun dato personale nei parametri GA4 (niente email, nome, telefono, indirizzo negli eventi o negli URL).

### 3.4 Shopify

Se il negozio è su Shopify: usare le app ufficiali dei canali (Facebook & Instagram, TikTok, Google & YouTube), che includono il lato server, e la Customer Privacy API di Shopify per collegare il banner. Gli eventi custom passano dai Customer Events (Web Pixels). Va controllato che app ufficiali e GTM non inviino lo stesso evento due volte.

## 4. UTM e nomi

Convenzione: tutto minuscolo, trattino basso come separatore.

| Parametro | Regola | Esempio |
|---|---|---|
| `utm_source` | piattaforma | `tiktok`, `meta`, `google`, `email`, `sms`, `creator_nomecreator` |
| `utm_medium` | tipo di traffico | `paid_social`, `cpc`, `shopping`, `email`, `sms`, `organic_social` |
| `utm_campaign` | ID campagna dell'app | `tiktok_vendite_lampadaclip_20261020` |
| `utm_content` | ID creatività | `cr-01a` |
| `utm_term` | solo per ricerca | parola chiave |

Su Meta e TikTok l'app usa i parametri dinamici della piattaforma per gli ID (campagna, gruppo, annuncio) così ogni ordine nel database si collega all'annuncio esatto. Nei video organici si usa un link in bio con UTM proprio (`utm_medium=organic_social`), altrimenti l'organico finisce in "diretto".

L'app salva le UTM del primo e dell'ultimo contatto nell'ordine (cookie di prima parte, solo con consenso statistiche; senza consenso si salvano solo le UTM della sessione d'acquisto, senza cookie persistente).

## 5. Domanda post-acquisto

Nella pagina di conferma ordine, facoltativa e senza dati personali:

> Come ci hai conosciuto?
> TikTok · Instagram · Facebook · Google · Un amico o un familiare · Un creator (quale?) · Altro: ______

La risposta si salva sull'ordine. Serve a vedere ciò che i pixel non vedono: passaparola, video condivisi in chat, persone che hanno visto un annuncio e poi cercato il nome del negozio. Va letta come indizio. Il 20% di risposte "TikTok" dice che TikTok fa conoscere il negozio, non che merita il 20% del credito.

## 6. Attribuzione

### 6.1 Cosa dice ogni fonte

| Fonte | Tende a | Perché |
|---|---|---|
| Meta / TikTok / Google Ads | Contare troppo se stessa | Finestre proprie, conversioni da sola visualizzazione, ognuna rivendica lo stesso ordine |
| GA4 | Dare troppo credito all'ultimo clic e al "diretto" | Perde utenti senza consenso e chi cambia dispositivo |
| Database ordini | È il conteggio vero | Ma senza UTM non sa da dove arriva l'ordine |
| Domanda post-acquisto | Premiare il contatto più memorabile | Ricordo impreciso |

### 6.2 Regole per l'app

1. Il numero di ordini e il ricavo vengono solo dal database dell'app.
2. Le conversioni delle piattaforme non si sommano mai tra loro. Se Meta rivendica 12 ordini e TikTok 9, e il database ne ha 15, gli ordini sono 15.
3. Finestra di attribuzione fissa e uguale per tutte le regole: 7 giorni dal clic. Le conversioni da sola visualizzazione si mostrano in una colonna separata e non entrano nelle regole di stop o scaling.
4. Metrica di controllo del negozio: MER = ricavo netto IVA del database / spesa ads totale. Se il MER a 7 giorni scende sotto il BE ROAS, gli aumenti di budget si bloccano anche quando il ROAS di piattaforma sembra buono.
5. Separare i clienti nuovi dai ritorni: un ordine di un cliente esistente arrivato da un annuncio di retargeting conta poco come prova che l'annuncio funziona.
6. Se una sola piattaforma è attiva (Fase 1), il confronto tra ordini rivendicati dalla piattaforma e ordini con la sua UTM nel database dà una stima di quanto la piattaforma si sovrastima. Va annotato, non trasformato in un moltiplicatore fisso.

### 6.3 Incrementalità

Con budget sotto qualche migliaio di euro al mese i test di incrementalità (geo holdout, gruppi di controllo) non raggiungono numeri leggibili. Si rimandano a quando la spesa mensile è stabile e una piattaforma pesa più del 50% del budget. Fino ad allora: MER, domanda post-acquisto e confronto prima/dopo quando si accende o spegne un canale.

### 6.4 Report settimanale

```markdown
# Lettura attribuzione, settimana [data]

Ordini (database): [N]   Ricavo netto: [€]   Spesa ads: [€]   MER: [x]   BE ROAS medio: [x]

| Canale | Ordini rivendicati dalla piattaforma (7d clic) | Ordini con UTM nel DB | "Come ci hai conosciuto" | Lettura |
|--------|----|----|----|----|

Note: consenso marketing accettato da [x]% delle sessioni. Ordini senza fonte: [N].
Decisione: [quale budget spostare e perché, con il livello di fiducia].
```

## 7. Verifica prima di spendere

- [ ] Banner: "Rifiuta" blocca davvero Meta e TikTok (controllo con gli strumenti sviluppatore del browser: nessuna richiesta a facebook.net o analytics.tiktok.com).
- [ ] Consent Mode: in GA4 DebugView e Tag Assistant i segnali di consenso cambiano dopo la scelta.
- [ ] Ordine di prova reale: `purchase` compare una sola volta in GA4, Meta Events Manager, TikTok Events Manager e Google Ads.
- [ ] Deduplicazione: in Meta Events Manager l'evento server e quello browser risultano deduplicati.
- [ ] Valore inviato = subtotale IVA esclusa, valuta EUR, `transaction_id` uguale all'ID ordine.
- [ ] Nessun dato personale negli URL e nei parametri GA4.
- [ ] UTM salvate sull'ordine nel database.
- [ ] Dominio verificato in Meta Business Manager e TikTok, eventi prioritari configurati dove richiesto.
- [ ] Rimborso di prova registrato con evento `refund` in GA4 e sottratto nel calcolo del MER.

## 8. Cosa resta manuale

- Configurazione e testi del banner cookie, scelta tra Consent Mode base e avanzato.
- Verifica dopo ogni modifica al tema del negozio o al checkout (i tag si rompono spesso lì).
- Lettura settimanale del report di attribuzione e decisioni di spostamento del budget.
