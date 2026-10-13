# 04 — Fonti di segnale per i prodotti in tendenza

> Data della ricerca: **13/10/2026**. Ogni dato ha fonte + URL. Dove non è stato possibile verificare un dato scrivo **DATO MANCANTE**.
>
> **Nota di metodo:** in questa sessione la rete in uscita non permetteva di aprire direttamente le pagine (fetch bloccato dal proxy aziendale, es. `developers.tiktok.com` → connessione rifiutata). I dati provengono dai risultati di ricerca web (snippet di pagine ufficiali quando disponibili, altrimenti fonti terze). Le fonti terze sono segnalate come tali. **Prima di scrivere codice di integrazione, ricontrollare ogni limite sulla documentazione ufficiale.**

---

## 1. Tabella riassuntiva

Legenda accesso: ✅ ufficiale e aperto · 🟡 ufficiale ma con requisiti/approvazione · 🔴 nessuna API ufficiale (solo UI, scraping vietato o rischioso).

| Fonte | Accesso | Costo | Requisiti | Rate limit | ToS / scraping | Utilità per il trend score |
|---|---|---|---|---|---|---|
| **Google Trends – API ufficiale** | 🟡 alpha su invito | Prezzo non pubblicato (DATO MANCANTE) | Candidatura; selezione a rotazione, preferenza a chi ha un caso d'uso concreto | DATO MANCANTE | Ufficiale → lecito | Alta: crescita ricerche, stagionalità (5 anni, dati non riscalati 0–100) |
| **Google Trends – pytrends / trendspy (non ufficiali)** | 🔴 | Gratis | Nessuno | Non pubblicato; errori 429 frequenti | Contro i ToS Google sulle query automatiche | Alta ma fragile |
| **Google Trends via SerpApi** | ✅ (terza parte) | Free 250 ricerche/mese; Starter $25/1.000; Developer $75/5.000; Production $150/15.000 | Account SerpApi | 50/h (free) – 3.000/h (Production) | Il rischio legale lo assume il fornitore ("U.S. Legal Shield" solo da $150) | Alta, costo prevedibile |
| **TikTok Creative Center (Top Products / Top Ads)** | 🔴 solo UI | Gratis (UI) | Account TikTok For Business | n/a | Nessuna API ufficiale per Top Products; gli "scraper" Apify non sono affiliati | Molto alta (prodotti nelle ads per Paese) – ma solo consultazione manuale |
| **TikTok Commercial Content API** | 🟡 | Gratis | Account TikTok for Developers + approvazione; fonti terze: riservata a ricercatori USA/UE | Fonti terze: ~1.000 richieste/giorno (non verificato) | Ufficiale | Media: ads UE per keyword/inserzionista, conservate 1 anno |
| **Amazon Best Sellers / Movers & Shakers** | 🔴 | — | — | — | Conditions of Use: vietati data mining, robot, estrazione di listing/prezzi | Alta, ma non accessibile legalmente in automatico |
| **Amazon Creators API (ex PA-API 5)** | 🟡 | Gratis | Iscrizione Amazon Associates del marketplace + **≥10 vendite qualificate negli ultimi 30 giorni** | DATO MANCANTE | Ufficiale; uso legato al programma affiliazione | Bassa per MVP (endpoint "best sellers" non trovato; requisito vendite) |
| **Keepa API** (dati Amazon, terza parte) | ✅ | Da ~€49/mese per 20 token/min (fonte terza) | Abbonamento | 20 token/min nel piano base; token scadono dopo 60 min | Servizio commerciale lecito | Alta: storico sales rank/prezzi, BSR per categoria |
| **AliExpress Open Platform / Affiliate API** | 🟡 | Gratis | Account affiliato/developer + approvazione (ore–3 giorni lavorativi secondo fonti terze); Order API richiede approvazione separata + OAuth | Fonti terze: 500 chiamate/giorno iniziali (non verificato) | Ufficiale | Alta: prezzo fornitore, ordini/volumi, `hotproduct.query` (nome metodo da fonte terza) |
| **CJdropshipping API 2.0** | ✅ | Gratis (account CJ) | API key da My CJ → Authorization → API | Free/livello 0–1: **1 req/s**; Plus 2, Prime 4, Advanced 6; account non verificati 1.000 chiamate/giorno per interfaccia; quota a punti dal 01/06/2026 | Ufficiale | Alta: catalogo, costo, magazzini (anche UE), spedizioni, evasione ordini |
| **Zendrop** | 🔴 | App da $0 / Pro $49 / Plus $79 | — | — | Nessuna API pubblica trovata | Bassa (solo come app Shopify) |
| **Spocket** | 🔴/🟡 | Starter $39,99 / Pro $59,99 / Empire $99,99 | Fonte terza: API limitata, pensata per le integrazioni Shopify/Woo | DATO MANCANTE | Nessuna doc pubblica trovata | Bassa (fornitori UE utili, ma solo via app) |
| **Shopify Admin API (GraphQL)** | ✅ | Gratis per le app (serve un negozio Shopify: Basic $39/mese mensile, $29 annuale) | App custom o pubblica; OAuth | Leaky bucket: **100 punti/s** Standard, 200 Advanced, 1.000 Plus, 2.000 Commerce Components; max 1.000 punti per query | Ufficiale | Non è una fonte di trend esterna: serve per **creare lo store/prodotti** e leggere le **nostre** vendite (feedback loop) |
| **Meta Ad Library API** (`/ads_archive`) | 🟡 | Gratis | App Meta developer + **verifica identità e posizione** su facebook.com/ID (alcuni giorni) | Rate limit non documentato nelle fonti trovate (DATO MANCANTE) | Ufficiale | Media-alta in UE: ads commerciali **consegnate in UE/UK** ricercabili per 1 anno (DSA art. 39), con `eu_total_reach`, targeting; spesa/impression solo per ads politiche |

### Fonti della tabella
- Google Trends API alpha (annuncio 24/07/2025, ancora candidature ad agosto 2026; nessuna GA né prezzo): PPC Land, https://ppc.land/google-opens-alpha-testing-for-new-trends-api-targeting-developers-and-journalists/ ; Konabayev "Google Trends API Landscape 2026", https://konabayev.com/blog/google-trends-api-landscape-2026/ ; ScrapeBadger, https://scrapebadger.com/blog/does-google-trends-have-an-api-what-to-use-in-2026 — consultati 13/10/2026 (fonti terze).
- pytrends archiviato il 17/04/2025, 429 e limite non pubblicato: DEV Community, https://dev.to/esteban_ortega/pytrends-is-dead-heres-how-to-get-google-trends-data-in-2026-1a18 ; apiserpent, https://apiserpent.com/blog/pytrends-dead-google-trends-data-2026 — 13/10/2026.
- ToS Google sulle query automatiche (testo storico + richiamo di Gary Illyes): https://policies.google.com/terms/archive/20051105 ; Search Engine Journal, https://www.searchenginejournal.com/google-warns-automated-queries-mean-third-party-tools/181385/ — **testo ToS 2026 attuale: DATO MANCANTE** (non verificato).
- SerpApi piani: https://serpapi.com/pricing.md ; SocialCrawl, https://www.socialcrawl.dev/blog/best-google-trends-apis-2026 — 13/10/2026. Se una query Trends conti 1:1 sulla quota: DATO MANCANTE.
- TikTok Top Products (pagina help, maggio 2025): https://ads.tiktok.com/help/article/top-products — 13/10/2026. Disponibilità del filtro "Italia": DATO MANCANTE (non verificato).
- TikTok Commercial Content API (ads UE, conservazione 1 anno, "public and researchers"): https://developers.tiktok.com/products/commercial-content-api ; annuncio TikTok 20/07/2023: https://newsroom.tiktok.com/tiktoks-research-api-and-commercial-content-library?lang=en-GB ; limite 1.000 req/giorno e restrizione ad accademici: AdMapix (fonte terza, in conflitto con la pagina ufficiale), https://www.admapix.com/blog/ad-intelligence/tiktok-ad-library-explained — 13/10/2026.
- Scraper Creative Center non ufficiali: Apify, https://apify.com/datapeak/tiktok-creative-center — 13/10/2026.
- Amazon Conditions of Use (divieto robot/data mining): copia su Scribd https://www.scribd.com/document/875709813/Amazon ; ConductAtlas https://conductatlas.com/platform/amazon/amazon-conditions-of-use/provision/CA-P-018441/prohibition-on-data-mining-and-scraping-tools/ — 13/10/2026 (fonti secondarie; verificare il testo live su amazon.it).
- PA-API 5 deprecata → Creators API (date in conflitto: 30/04 o 15/05/2026): https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation ; requisito 10 vendite/30 giorni: https://affiliate-program.amazon.com/creatorsapi/docs/ — 13/10/2026.
- Keepa: modello a token, https://keepa.com/api-docs/plans-tokens.html ; €49/mese 20 token/min (fonte terza, agg. 22/07/2026): https://revenuegeeks.com/software/keepa/api — 13/10/2026.
- AliExpress API (accesso, 500/giorno, firma HMAC, metodo hotproduct): Rapidevelopers https://www.rapidevelopers.com/md/bubble-integrations/aliexpress-api ; Jentic https://www.jentic.com/apis/aliexpress — 13/10/2026 (**solo fonti terze**; doc ufficiale open.aliexpress.com non verificata).
- CJdropshipping limiti: https://developers.cjdropshipping.com/en/api/start/limit.html ; punti: https://developers.cjdropshipping.com/en/api/api2/standard/points.html ; API key: https://developers.cjdropshipping.cn/en/summary/course.html — 13/10/2026 (doc ufficiale; due versioni di pagina riportano cifre base diverse, 10/30 vs 100 req/s).
- Zendrop/Spocket prezzi: ecommerce-platforms.com, https://ecommerce-platforms.com/articles/spocket-vs-zendrop ; affmaven, https://affmaven.com/spocket-pricing-plans/ ; API Spocket: Rapidevelopers, https://rapidevelopers.com/bolt-ai-integrations/spocket — 13/10/2026 (fonti terze). API Zendrop: **nessuna evidenza trovata**.
- Shopify rate limit: https://shopify.dev/docs/apps/build/apis/graphql-admin/rate-limits — 13/10/2026 (ufficiale). Prezzo Basic $39/$29: Sellfy https://sellfy.com/it/blog/prezzi-shopify/ ; prezzo in **euro** per l'Italia: DATO MANCANTE (pagina https://it.shopify.com/pricing non leggibile da qui).
- Meta Ad Library: verifica identità facebook.com/ID e ads commerciali solo se consegnate in UE/UK: Zernio docs https://docs.zernio.com/platforms/meta-ads/ad-library ; adlibrary.com https://adlibrary.com/posts/eu-dsa-ad-repositories-developers ; metapi https://metapi.io/compare/facebook-ad-library-api — 13/10/2026 (fonti terze; doc ufficiale Meta non leggibile da qui).

---

## 2. Cosa significa per noi (Italia/UE)

1. **Il "segnale TikTok/Amazon" che vendono i competitor non è ottenibile legalmente via API da noi.** Top Products di TikTok e Best Sellers di Amazon esistono solo come interfaccia; automatizzarli = scraping contro ToS. I competitor (Minea, PiPiAds, Kalodata…) lo fanno con i loro crawler: noi non dobbiamo copiarli.
2. **Essere in UE è un vantaggio sulle ads**: grazie al DSA (art. 39) Meta e TikTok espongono anche le ads **commerciali** consegnate in UE. Meta Ad Library API è la fonte di "ads attive" più solida e gratuita, previa verifica identità.
3. **Google Trends resta il segnale di domanda migliore**, ma: API ufficiale = alpha a inviti; librerie non ufficiali = fragili e contro i ToS. Per un MVP onesto → **SerpApi** (free 250/mese per prototipare, poi $25–75/mese) e candidatura all'alpha in parallelo.
4. **Lato offerta/margine** abbiamo API ufficiali e gratuite: **CJdropshipping** (costi, magazzini UE, spedizioni) e **AliExpress Affiliate API** (prezzi, volumi ordini).
5. **Vincolo regolatorio nuovo:** dal **01/07/2026** dazio fisso UE di **€3 per articolo** sulle spedizioni extra-UE ≤ €150 (Reg. UE 2026/382, temporaneo fino al 2028) — va dentro il calcolo del margine. Fonti: Mysolution 18/05/2026 https://www.mysolution.it/fisco/informazioni/news/2026/05/18/e-commerce-dazio-di-3-euro-sui-piccoli-pacchi-dal-1-luglio/ ; Teleborsa 30/06/2026 https://www.teleborsa.it/DettaglioNews/35_2026-06-30_TLB/Ue-dazio-di-3-euro-sui-mini-pacchi-da-Cina-e-Paesi-extra-UE-al-via-dal-1-luglio.html ; per-articolo vs per-pacco: le fonti divergono (Fiscal Focus/Dogane: per articolo, https://www.fiscal-focus.it/news,186100 ; Fisco e Tasse: per pacco, https://www.fiscoetasse.com/new-rassegna-stampa/3540-tassa-unionale-sui-pacchi-di-piccolo-valore-in-vigore-da-luglio.html). Il contributo italiano di €2 risulta sospeso (stessa fonte Fisco e Tasse).
6. **GPSR** (Reg. UE 2023/988, applicabile dal 13/12/2024): il dropshipping rientra; servono dati fabbricante/responsabile UE, tracciabilità, avvertenze. Fonte: Commissione UE, https://trade.ec.europa.eu/access-to-markets/it/news/regolamento-sulla-sicurezza-generale-dei-prodotti-gpsr-dellue-una-nuova-era-la-tutela-dei — 13/10/2026. Ripartizione esatta degli obblighi nel dropshipping: DATO MANCANTE (verificare artt. 15–16 su EUR-Lex). → Nel trend score i prodotti senza dati GPSR del fornitore vanno **esclusi**, non penalizzati.

---

## 3. Raccomandazione per l'MVP

**Stack MVP (solo canali ufficiali o fornitori commerciali, zero scraping):**

| Ruolo | Fonte | Costo stimato | Priorità |
|---|---|---|---|
| Domanda (crescita, stagionalità) | SerpApi → Google Trends (geo=IT) | $0 (250/mese) → $25–75/mese | P0 |
| Domanda (ufficiale, futuro) | Candidatura Google Trends API alpha | DATO MANCANTE | P1 (in parallelo) |
| Ads attive / saturazione | Meta Ad Library API (`ad_reached_countries=IT`) | Gratis | P0 |
| Costo, magazzino, spedizione | CJdropshipping API 2.0 | Gratis (1 req/s su free) | P0 |
| Prezzo e volumi ordini | AliExpress Affiliate API | Gratis | P1 |
| Domanda Amazon (opz.) | Keepa API | ~€49/mese | P2 (solo se il budget lo consente) |
| Store e feedback vendite | Shopify Admin GraphQL API | negozio Shopify | P0 (esecuzione, non segnale) |
| TikTok Creative Center | Consultazione **manuale** dell'operatore, input umano nella UI dell'app | Gratis | P1 |

**Escludere dall'MVP:** scraping di Amazon Best Sellers/Movers & Shakers, scraping di TikTok Creative Center, pytrends in produzione, Zendrop/Spocket come fonti dati (nessuna API pubblica documentata).

**Pattern "degrada con grazia"** (coerente col resto del repo): ogni collector ha un `source` (`SERPAPI`, `META_ADLIB`, `CJ`, `MOCK`). Senza chiave → mock dichiarato, mai spacciato per reale; segnale mancante → `DATO MANCANTE` e il prodotto perde punti di **completezza**, non riceve un valore inventato.

---

## 4. Proposta di "Trend Score" (0–100)

### 4.1 Segnali (ognuno normalizzato 0–1)

| # | Segnale | Fonte | Calcolo proposto | Peso |
|---|---|---|---|---|
| S1 | **Crescita ricerche** | Google Trends (IT, 90 gg) | pendenza della media 4 settimane recenti vs 8 precedenti; `clip((ratio−1)/1, 0, 1)` | 0,25 |
| S2 | **Ads attive (domanda validata)** | Meta Ad Library (IT/UE) | n. inserzionisti distinti con ads attive sulla keyword negli ultimi 30 gg; curva a campana: pochi (3–15) = 1, zero = 0,2, troppi → vedi S6 | 0,15 |
| S3 | **Margine unitario** | CJ/AliExpress + prezzo di vendita stimato | `(P_vend − costo − sped − €3 dazio se extra-UE − commissioni − CPA stimato) / P_vend`; 0 se < 20%, 1 se ≥ 45% | 0,25 |
| S4 | **Peso / spedizione** | CJ (peso, magazzino UE, giorni) | 1 se magazzino UE e ≤ 7 gg e ≤ 500 g; 0 se > 2 kg o > 20 gg | 0,10 |
| S5 | **Stagionalità** | Google Trends 5 anni | 1 se il picco storico atteso è tra 3 e 8 settimane da oggi; 0 se il picco è appena passato | 0,10 |
| S6 | **Saturazione** (penalità) | Meta Ad Library + n. venditori AliExpress/CJ | `1 − clip(inserzionisti_IT / 50, 0, 1)` | 0,15 |

`score = 100 × Σ(w_i × S_i)` calcolato **solo sui segnali disponibili**, poi:

- `completezza = Σ pesi dei segnali disponibili` (0–1).
- **Regole dure (non opinioni, da testare come nel progetto WorldCupEdge):**
  - completezza < 0,60 → **SKIP** (`DATO MANCANTE`, nessun punteggio mostrato);
  - margine S3 netto < 20% → **SKIP** a prescindere dal resto;
  - prodotto in categoria vietata/regolata (cosmetici senza PIF, giocattoli senza CE, elettronica senza CE/RAEE, integratori, dispositivi medici) o senza dati GPSR → **ESCLUSO**;
  - mai etichette tipo "prodotto vincente sicuro": solo livelli di confidenza ALTA (≥ 70 e completezza ≥ 0,85) / MEDIA (≥ 55) / BASSA (< 55) / INSUFFICIENTE (completezza < 0,60).

### 4.2 Perché questi pesi
Margine e domanda (S1+S3 = 50%) dominano perché sono gli unici due segnali che determinano se un test di ads può andare in pareggio; ads attive e saturazione sono speculari (bilanciamento "c'è mercato" vs "è già affollato"). I pesi sono un **punto di partenza da calibrare** sul backtest delle nostre vendite reali (stesso principio del repo: il backtest è il gate prima del denaro reale).

### 4.3 Validazione
- Registrare per ogni prodotto testato: score al giorno 0, spesa ads, CPA, ROAS a 14 giorni.
- Dopo ≥ 30 prodotti testati: regressione logistica "ROAS ≥ 1,5 sì/no" sui segnali → aggiornare i pesi.
- Finché non c'è questo storico, il punteggio è un **filtro di scrematura**, non una previsione di profitto.
