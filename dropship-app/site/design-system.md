# Design system — store generati (mobile-first)

Fonte dei valori: `design-tokens.json` (primitive → semantic → component).
Implementazione: `template/assets/store.css` (CSS custom properties, ~10 KB, zero
framework, zero JavaScript). Brand e voce: `BRAND.md`.

## 1. Principi

1. **Chiarezza prima della persuasione.** Prezzo IVA inclusa, costo e tempi di
   spedizione, resi 14 giorni e contatti sono visibili *sopra la piega o subito
   sotto*, senza aprire nulla. Sono la nostra "social proof" onesta.
2. **Un solo CTA caldo.** Il colore `cta` (terracotta) compare solo sul pulsante
   d'acquisto. Tutto il resto è neutro o `brand`.
3. **Mobile-first reale.** Progettato a 390px; il desktop è un'estensione
   (galleria a sinistra sticky, info a destra).
4. **Veloce per costruzione.** Un CSS, due font self-hosted (`.woff2` variabili,
   ~66 KB totali, `font-display: swap`, preload del solo Rubik), immagini con
   `width/height` (CLS ≈ 0), prima immagine `fetchpriority="high"`, le altre `lazy`.
5. **Onesto per costruzione.** Il template non ha slot per countdown, contatori
   di visitatori, "ultimi pezzi" o badge inventati. Vedi §7.

## 2. Token in breve

| Gruppo | Token CSS | Valori |
|--------|-----------|--------|
| Brand (personalizzabile) | `--c-brand`, `--c-brand-strong`, `--c-brand-soft` | default `#0F5E57`, `#0B4A44`, `#E6F2F0` |
| CTA (fisso) | `--c-cta`, `--c-cta-strong`, `--c-on-cta` | `#C2410C`, `#9A3412`, `#FFFFFF` (5.18:1) |
| Neutri | `--c-bg`, `--c-surface`, `--c-border`, `--c-text`, `--c-text-muted`, `--c-text-subtle` | `#FFF`, `#F7F6F3`, `#E7E5E4`, `#1C1917`, `#57534E`, `#78716C` |
| Stato | `--c-success`, `--c-danger`, `--c-notice` (+ `-soft`) | `#15803D`, `#B91C1C`, `#92400E` |
| Font | `--f-display` Rubik · `--f-body` Nunito Sans | fallback `system-ui` |
| Scala tipo | `--fs-xs … --fs-4xl` | 14 · 15 · 16 · 18 · 22 · 26 · 32 · 40 px |
| Spazi | `--s-1 … --s-8` | 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 px |
| Raggi | `--r-sm/md/lg/pill` | 6 · 10 · 16 · 999 px |
| Target tocco | `--tap` | 48px (≥ 44px) |
| Breakpoint | — | 480 · 768 · 1024 · 1280 px (min-width) |

**Personalizzazione per store:** il generatore può cambiare solo i tre `--c-brand*`
(stile inline nel `<head>`), e deve verificare contrasto ≥ 4.5:1 tra bianco e
`brand` prima di accettarlo; altrimenti usa il default. CTA e neutri non si
toccano: garantiscono leggibilità e gerarchia su ogni store.

Niente dark mode negli store, per scelta: le foto prodotto dei fornitori sono su
fondo bianco e su fondo scuro peggiorano; la coerenza conta più della variante.

## 3. Componenti

| Componente | Classe | Note |
|------------|--------|------|
| Barra info | `.topbar` | spedizione · tempi · resi. Solo fatti, mai urgenza |
| Header | `.site-header`, `.nav` | ≤ 4 voci; su mobile "Spedizioni/Resi" spariscono (restano in topbar e footer) |
| Breadcrumb | `.breadcrumb` | rispecchia l'URL: Home › Categoria › Prodotto |
| Galleria | `.gallery` | mobile: carosello scroll-snap nativo (no JS), 88% di larghezza per far intuire lo scorrimento; desktop: principale + griglia 3 colonne |
| Prezzo | `.price-block`, `.price-note` | prezzo grande; "IVA inclusa" + spedizione subito sotto |
| Prezzo di riferimento | `.price-ref` | SOLO "prezzo più basso degli ultimi 30 giorni" |
| Bullet benefici | `.bullets` | 3–5 righe, check SVG decorativo |
| CTA primario | `.btn.btn-primary` | 52px, testo "Aggiungi al carrello" |
| CTA secondario | `.btn.btn-secondary` | contorno brand |
| Info spedizione/resi/garanzia | `.info-list > .info-row` | icona SVG inline + titolo + 1 riga + link alla pagina completa |
| Avviso neutro | `.notice` | es. spedizione extra-UE. Ambra, non rosso |
| Accordion | `details.acc` | HTML nativo: accessibile da tastiera senza JS |
| Recensioni | `.review-list`, `.reviews-empty` | vedi §7 |
| Contatti | `.contact-card` | email sempre; telefono opzionale |
| Footer legale | `.site-footer`, `.legal-line` | ragione sociale, indirizzo, P.IVA, REA/PEC, link privacy/cookie/condizioni |
| Barra acquisto sticky | `.buy-bar` | solo < 768px: prezzo + CTA sempre raggiungibili col pollice; usa `form="buy-form"`, rispetta `safe-area-inset-bottom` |
| Bozza legale | `.draft-banner`, `.ph` | banner "BOZZA" e campi da compilare evidenziati |

Stati del pulsante: default `cta` → hover `cta-strong` (150ms) → focus anello
3px `brand` con offset 2px → disabilitato `border` + `text-muted`,
`aria-disabled="true"`. `prefers-reduced-motion` azzera le transizioni.

## 4. Architettura del sito generato

```
Home (/)
├── Prodotto (/prodotti/{slug})            ← pagina d'atterraggio delle ads
├── Spedizioni (/legal/spedizioni)
├── Resi e rimborsi (/legal/resi)
├── Privacy (/legal/privacy)
├── Cookie (/legal/cookie)
└── Condizioni di vendita (/legal/termini)
```

- Tutto a ≤ 2 click dalla home; pagine legali raggiungibili da ogni footer
  (nessuna pagina orfana). URL minuscoli, con trattini, senza ID.
- Header: Prodotti · Spedizioni · Resi · Contatti. Footer: Assistenza / Note
  legali / Pagamenti + riga legale.
- Pagine legali `noindex` finché sono in bozza.
- Store mono-prodotto: la home può reindirizzare al prodotto, ma le pagine
  legali restano identiche.

## 5. Scelte di conversione (CRO), e cosa NON facciamo

Ordine della pagina prodotto sul mobile, per obiezione del cliente:
1. *"Cos'è?"* → foto + titolo chiaro. 2. *"Quanto costa davvero?"* → prezzo IVA
inclusa + spedizione. 3. *"Fa per me?"* → 3–5 bullet. 4. *"Compro"* → CTA (anche
sticky). 5. *"Quando arriva? E se non mi piace?"* → righe spedizione/resi/garanzia
subito sotto il CTA. 6. *"Chi siete?"* → contatti e dati aziendali.

Ipotesi da testare (A/B, non da dare per vere): titolo orientato al beneficio vs
descrittivo; bullet sopra vs sotto il prezzo; foto "in uso" come prima immagine;
"Consegna entro il {data}" (calcolata dai dati reali) vs intervallo in giorni.

Non usiamo: countdown, popup d'uscita con sconto, "X persone stanno guardando",
"ordinato da Mario 3 minuti fa", stelle senza recensioni, prezzi barrati non
conformi, badge "certificato"/"originale" senza prova. Oltre a essere pratiche
commerciali scorrette (D.Lgs. 206/2005, artt. 20–23), distruggono la fiducia che
è il nostro unico vantaggio.

## 6. Segnaposto dei template (sintassi Mustache)

`{{x}}` testo con escape · `{{{x}}}` HTML (sanificato dal generatore!) ·
`{{#x}}…{{/x}}` se vero / per ogni elemento · `{{^x}}…{{/x}}` se falso o vuoto.
Renderer di riferimento a sola standard library: `tools/render.py`.

| Segnaposto | Tipo | Note |
|------------|------|------|
| `store_name`, `store_tagline`, `store_logo_url` | testo / URL opz. | |
| `theme_brand`, `theme_brand_strong`, `theme_brand_soft` | hex | contrasto verificato (§2) |
| `assets_base`, `base_url`, `canonical_url` | percorso | `assets_base` relativo (es. `assets/`); le pagine legali lo prefissano con `../` |
| `meta_description`, `og_image`, `year` | testo | |
| `title`, `subtitle`, `sku`, `category`, `category_url` | testo | |
| `price` | testo formattato | `€ 29,90` (formato italiano) |
| `price_number` | numero | `29.90` per JSON-LD |
| `price_reference`, `discount_label` | testo opz. | SOLO prezzo più basso degli ultimi 30 gg (art. 17-bis Cod. Consumo); altrimenti `null` |
| `in_stock` | bool | solo da sincronizzazione reale col fornitore |
| `images[]` | `{src, srcset?, alt, width, height}` | `loading`, `fetchpriority`, `last` aggiunti dal renderer |
| `bullets[]` | stringhe | 3–5 |
| `description_html`, `specs[] {label, value_html}` | HTML sanificato | |
| `payment_methods_label` | testo | solo metodi realmente attivi |
| `shipping_cost_label`, `shipping_days_min`, `shipping_days_max`, `shipping_days_late`, `handling_days` | testo / numeri | dai dati del fornitore/corriere |
| `ships_from`, `ships_from_outside_eu`, `carrier` | testo / bool | se extra-UE l'avviso è obbligatorio |
| `duties_included`, `duties_label` | bool / testo | `true` solo con IOSS o costi assorbiti dal venditore |
| `return_days`, `return_cost_label` | numero (≥ 14) / testo | |
| `contact_email`, `contact_phone`, `contact_phone_e164`, `contact_hours`, `contact_response_time` | testo | email obbligatoria |
| `reviews[] {author, date, date_iso, rating, stars, text, verified}` | lista | vedi §7; `has_reviews` lo calcola il renderer |
| `reviews_avg`, `reviews_count`, `reviews_policy_label` | | calcolati sulle sole recensioni reali |
| `company_name`, `company_address`, `vat_number`, `rea`, `pec`, `share_capital` | testo | P.IVA obbligatoria; gli altri se dovuti |
| `hero_title`, `hero_text`, `hero_cta_url`, `hero_cta_label`, `hero_image{}` | home | |
| `products_title`, `products[] {url, title, price, lowest_30d, image_src, image_alt}` | home | |
| `legal_updated_at`, `return_cost_policy`, `return_address`, `privacy_email`, `platform_provider`, `supplier_name_country`, `payment_provider`, `cookie_name` | pagine legali | |

**Attenzione (Mustache):** dentro una sezione lista, una chiave assente
nell'elemento viene cercata nel contesto padre. Per questo nei `products[]` il
prezzo di riferimento si chiama `lowest_30d` (non `price_reference`) e il
generatore deve impostarlo sempre, anche a `null`. È stato un bug reale trovato
nell'anteprima: senza questa regola ogni card mostrava il prezzo barrato del
prodotto principale.

## 7. Regole non negoziabili (da coprire con test nel generatore)

1. **Recensioni:** solo da ordini reali dello store (o importate con fonte
   dichiarata in `reviews_policy_label`, come richiesto dall'art. 22 c. 4-bis Cod.
   Consumo). `reviews` vuoto → messaggio "non ha ancora recensioni", niente stelle,
   niente `aggregateRating` nel JSON-LD. Mai recensioni copiate dal fornitore
   spacciate per clienti dello store.
2. **Niente urgenza falsa:** nessun timer, nessun contatore di scorte se non
   collegato al magazzino reale, nessuna "offerta che scade" senza data reale.
3. **Prezzo barrato** solo con `price_reference` = minimo 30 giorni.
4. **Tempi di consegna** sempre come intervallo dai dati del fornitore; se il
   dato manca, il generatore non pubblica la pagina (non inventa "3–5 giorni").
5. **Origine extra-UE** dichiarata sulla pagina prodotto e in Spedizioni.
6. **Footer legale** completo (ragione sociale, sede, P.IVA) su ogni pagina.
7. **Pagine legali** restano marcate "BOZZA" finché un professionista non le
   ha riviste.
8. **Cookie:** il template usa solo cookie tecnici; aggiungere pixel/analytics
   richiede banner di consenso conforme prima della pubblicazione.

## 8. Accessibilità (checklist applicata)

- Contrasti verificati (tabella in `BRAND.md` §4), testo minimo 14px, base 16px.
- `lang="it"`, skip link, landmark (`header/nav/main/footer`), breadcrumb con
  `aria-current`, un solo `h1`, gerarchia h2/h3.
- Focus visibile ovunque (`:focus-visible`), target ≥ 48px, accordion e
  carosello senza JS (tastiera nativa), icone SVG `aria-hidden` con testo accanto.
- `alt` descrittivo obbligatorio per ogni immagine prodotto; il generatore lo
  scrive, non usa il nome file.
- Stato "disponibile" con icona + testo (non solo colore).
- `prefers-reduced-motion` rispettato; zoom non bloccato.

## 9. Anteprime

`python3 tools/build_preview.py` e poi
`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers NODE_PATH=$(npm root -g) node tools/screenshot.cjs`
→ `preview-mobile.png` (primo schermo 390×844 @2x, con barra sticky),
`preview-desktop.png` (1440, pagina intera), `preview/product-mobile-full.png`,
`preview/home-desktop.png`. Tutti i dati sono di esempio (`preview/sample-data.json`)
e le pagine portano la fascia "ANTEPRIMA — DATI DI ESEMPIO".

## 10. Font

Rubik e Nunito Sans, SIL Open Font License 1.1 (uso commerciale e
ridistribuzione consentiti), scaricati da Google Fonts e serviti in locale da
`template/assets/fonts/`. Mantenere il file di licenza OFL accanto ai font.
