# 06 — Fonti di discussione per scoprire problemi reali (problem mining)

> Data della ricerca: **13/10/2026**. Ogni dato ha fonte + URL + data di consultazione. Dove non ho trovato il dato scrivo **DATO MANCANTE**.
>
> **Nota di metodo:** in questa sessione **WebFetch è bloccato dal proxy** (es. `redditinc.com/policies/data-api-terms` → "unable to fetch"). Tutti i dati vengono dagli snippet della ricerca web: pagine ufficiali quando c'erano, altrimenti fonti terze, segnalate come tali. **Prima di attivare una fonte, rileggere i termini ufficiali** (link in tabella).
>
> Codice: `app/dropship/problems/`. Test: `app/tests/test_problems.py` (45 test, nessuna chiamata di rete).

---

## 1. Perché "analizzare ogni singolo sito" non è fattibile né lecito

1. **Contratto (ToS).** La maggior parte dei siti con discussioni utili (Amazon, Trustpilot, Quora, Facebook, TikTok, Google) vieta nei termini d'uso la raccolta automatica fuori dalle API ufficiali. Violarli è una violazione contrattuale e porta a ban di IP/account. Il caso più grosso: **Google ha fatto causa a SerpApi il 19/12/2025** (N.D. Cal., n. 25-10826) per aver aggirato le protezioni anti-scraping della SERP. A febbraio 2026 SerpApi ha chiesto il rigetto (motion to dismiss) e il caso risulta ancora aperto ([IPWatchdog 26/12/2025](https://ipwatchdog.com/2025/12/26/google-sues-serpapi-parasitic-scraping-circumvention-protection-measures/), [PPC Land](https://ppc.land/google-sues-serpapi-over-search-scraping-in-copyright-lawsuit/), consultati il 13/10/2026).
2. **Diritto sui generis sulle banche dati** (Dir. 96/9/CE; in Italia art. 102-bis L. 633/1941). Estrarre in modo sistematico parti sostanziali di un forum può violarlo anche se il sito non lo vieta espressamente. Molti editori italiani lo scrivono comunque nei termini: per esempio Alvolante vieta "estrazione e reimpiego" dei contenuti con qualunque mezzo ([alvolante.it/condizioni_uso](https://www.alvolante.it/condizioni_uso)), e Cosedicasa usa una formula quasi identica ([cosedicasa.com/condizioni-uso](https://www.cosedicasa.com/condizioni-uso)) — 13/10/2026.
3. **GDPR.** I post pubblici restano dati personali: servono base giuridica (legittimo interesse con test di bilanciamento), minimizzazione e trasparenza. L'EDPB ha adottato le **Linee guida 03/2026 sul web scraping** (07/07/2026, in consultazione fino al 30/10/2026). Il Garante italiano ha pubblicato nel 2024 indicazioni anti-scraping (G.U. 07/06/2024) ([Cybersecurity360](https://www.cybersecurity360.it/news/web-scraping-le-nuove-linee-guida-edpb-per-lera-dellai-generativa/), [Agenda Digitale](https://www.agendadigitale.eu/sicurezza/privacy/web-scraping-per-addestrare-lai-tutti-i-paletti-delledpb/), [datenschutz-notizen](https://www.datenschutz-notizen.de/how-to-protect-data-from-web-scraping-guidelines-from-the-italian-dpa-4448630/) — fonti secondarie, 13/10/2026). Il testo ufficiale EDPB non l'ho letto: **DATO MANCANTE** sulle formulazioni esatte.
4. **Tecnica e costo.** Ogni sito ha HTML, paginazione e anti-bot diversi: mantenere migliaia di scraper è un lavoro a tempo pieno, fragile, e i proxy residenziali per aggirare i blocchi sono esattamente ciò che non vogliamo fare.

**Conclusione:** lavoriamo con poche fonti, **lecite per costruzione**: API ufficiali con termini compatibili e feed RSS/Atom che i siti pubblicano apposta per essere letti. Il codice rifiuta i domini vietati anche se qualcuno li configura per errore (`DENIED_DOMAINS` in `sources.py`).

---

## 2. Tabella delle fonti

Legenda: ✅ ammessa e implementata · 🟡 ammessa con condizioni (implementata ma disattivata finché non ci sono le condizioni) · 🔴 esclusa.

| Fonte | Accesso | Costo | Limiti | ToS: uso commerciale / scraping | Dati personali / GDPR | Italiano | Stato nel codice |
|---|---|---|---|---|---|---|---|
| **Reddit Data API** | API ufficiale OAuth | Gratis non commerciale; commerciale **a contratto**. Le cifre circolanti ($0,24/1.000 chiamate, impegni da $12.000) non sono confermate su pagine Reddit attuali → DATO MANCANTE | 100 query/min per client OAuth (fonti terze, media su 10 min) | Dal **11/11/2025** l'accesso self-service è chiuso: serve approvazione (*Responsible Builder Policy*). L'uso commerciale richiede un accordo separato | Bisogna cancellare i contenuti rimossi su Reddit; raccomandato non conservarli oltre 48h (fonte terza) | Sì (r/italy, r/Italia, sub tematici) | 🟡 `RedditSource`, attivo solo con `REDDIT_API_APPROVED=1`; retention 2 giorni |
| **Stack Exchange API 2.3** | API ufficiale | Gratis | 300 req/giorno per IP senza chiave, 10.000 con chiave (fonti terze); il campo `backoff` va rispettato | Contenuti **CC BY-SA**: serve attribuzione con link. Per raccolta finalizzata all'AI generativa, una fonte terza parla di consenso scritto (non riguarda il nostro uso) | Non leggiamo `owner` | Quasi solo EN (diy, lifehacks, cooking, outdoors, parenting) | ✅ `StackExchangeSource` |
| **YouTube Data API v3 (commenti)** | API ufficiale | Gratis | 10.000 unità/giorno di default; `search.list` costa 100, `commentThreads.list` costa 1 | Uso commerciale ammesso dalle Developer Policies. I dati vanno cancellati o aggiornati **entro 30 giorni** | Non leggiamo `authorDisplayName`/`authorChannel*` | Sì (`relevanceLanguage=it`, `regionCode=IT`) | ✅ `YouTubeCommentsSource`, con budget quota lato client e retention 30 giorni |
| **Hacker News (Algolia HN Search)** | API pubblica senza chiave | Gratis | ~10.000 req/ora per IP; max 1.000 risultati per query (fonti terze) | Termini specifici dell'API: DATO MANCANTE | Non leggiamo `author` | No (EN, pubblico tech: poco rappresentativo del consumatore IT) | ✅ `HackerNewsSource`, attivo con `DROPSHIP_ENABLE_HN=1` |
| **RSS/Atom di forum e testate** (incl. Discourse `/latest.rss`) | Feed pubblicato dal sito | Gratis | Il codice applica il `Crawl-delay` di robots.txt, con minimo 5 s per dominio | Il feed è pensato per la lettura, ma i ToS di molti editori IT vietano l'estrazione (vedi §1.2) → **verifica manuale per ogni sito** prima di aggiungerlo | Testo ripulito da email, @utente e telefoni; nessun autore | Sì, ed è la fonte IT principale | ✅ `RssSource`: solo feed in `DROPSHIP_PROBLEM_RSS_FEEDS`, solo HTTPS, robots.txt rispettato |
| **Discourse pubblici (JSON)** | `latest.json`/`search.json` senza login | Gratis | ~60 req/min anonimo secondo una fonte terza, "nessun limite" secondo un'altra → DATO MANCANTE | Dipende dal singolo forum | Come RSS | Dipende dal forum | Coperto via **RSS** (`/latest.rss`, `/c/<cat>.rss`) ([meta.discourse.org](https://meta.discourse.org/t/discourse-rss-feeds/264134)). Adapter JSON non fatto: non serve |
| **Forum italiani** (Alfemminile, HDblog, forum di testate) | Solo dove esiste un feed | — | — | ToS di Alfemminile: **DATO MANCANTE** (non trovati). Feed HDblog/Alfemminile: **DATO MANCANTE** (non trovati) | — | Sì | Da valutare uno per uno, poi aggiungere a `DROPSHIP_PROBLEM_RSS_FEEDS` |
| **Quora** | Nessuna API pubblica | — | — | I ToS permettono l'accesso solo tramite le "interfacce pubblicate" (frammento riportato da terzi) | — | Parziale | 🔴 escluso |
| **Gruppi Facebook** | Groups API **dismessa** con Graph API v19, effettiva dal 22/04/2024 | — | — | Scraping vietato | Dati personali sensibili (gruppi chiusi) | Sì | 🔴 escluso |
| **TikTok Research API** | API ufficiale, solo ricercatori **non-profit** (USA, Europa, Canada, Brasile) | Gratis | DATO MANCANTE | Non adatta a uso commerciale: una domanda è stata respinta anche per "interessi commerciali non dichiarati" | — | Sì | 🔴 escluso (non idonei) |
| **Recensioni Amazon** | Nessuna API: PA-API 5 non restituisce le recensioni (dal 2020) | — | — | Le Conditions of Use vietano robot e data mining (vedi doc 04) | — | Sì | 🔴 escluso |
| **Trustpilot** | Business API solo per **la propria** azienda (account Business + modulo API) | A pagamento: DATO MANCANTE | DATO MANCANTE | I termini vietano text/data mining e scraping senza permesso (fonte terza) | — | Sì | 🔴 escluso (riconsiderare solo per le recensioni del **nostro** negozio) |
| **Google "People also ask" / autocomplete (via SerpApi)** | Nessuna API Google; solo rivenditori di SERP | SerpApi: prezzi nel doc 04; DataForSEO autocomplete $0,0006/req (concorrente) | — | I ToS Google vietano le query automatiche; causa Google contro SerpApi pendente | Basso (sono query, non post) | Sì | 🔴 escluso per ora: rischio legale non nostro ma ereditato. Rivalutare a causa chiusa |
| **Product Hunt API v2** | API ufficiale GraphQL | Gratis | DATO MANCANTE | La documentazione dice che l'API **non può essere usata per scopi commerciali** senza permesso (hello@producthunt.com) | — | No | 🔴 escluso (scrivere a PH se serve) |

### Fonti della tabella (consultate il 13/10/2026)
- Reddit, rate limit e prezzi (fonti terze, in conflitto tra loro): [SocialCrawl](https://www.socialcrawl.dev/blog/reddit-api-key-limits-alternatives-2026), [Techloy](https://www.techloy.com/reddit-api-pricing-in-2026-complete-guide-for-developers-and-businesses/), [Octolens](https://octolens.com/blog/reddit-api-pricing). Responsible Builder Policy dell'11/11/2025 (copia del thread r/redditdev): [mirror](https://r.datuan.dev/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/noh6fun). Obbligo di cancellazione e raccomandazione 48h (fonte terza): [ScrapeBadger](https://scrapebadger.com/blog/reddit-api-vs-scraping-the-honest-2026-comparison), [Postiz](https://postiz.com/blog/reddit-api-limits-rules-and-posting-restrictions-explained). Termini ufficiali **non letti** (fetch bloccato): https://redditinc.com/policies/data-api-terms.
- Stack Exchange, quote (fonti terze): [apis.io](https://apis.io/rate-limits/stackexchange/stackexchange-rate-limits/), [rollout.com](https://rollout.com/integration-guides/stack-exchange/api-essentials). Uso commerciale del CC (post del 2010): [stackoverflow.blog](https://stackoverflow.blog/2010/08/11/defending-attribution-required). Restrizione AI sul data dump (2024): [DevClass](https://devclass.com/2024/07/30/stack-exchange-restricts-access-to-dump-of-user-contributed-data-as-critics-complain-license-permits-reuse-for-any-purpose). Termini API ufficiali: https://stackexchange.com/legal/api-terms-of-use (**non letti**).
- YouTube, quote: [developers.google.com/youtube/v3/determine_quota_cost](https://developers.google.com/youtube/v3/determine_quota_cost) (ufficiale). Regola dei 30 giorni: [Developer Policies guide](https://developers.google.com/youtube/terms/developer-policies-guide) (ufficiale). Modifica del 01/06/2026 sulle statistiche: [revision history](https://developers.google.cn/youtube/terms/revision-history).
- HN Algolia, limite 10.000/h (fonti terze): [npm hacker-news-api](https://npmjs.com/package/hacker-news-api). Documentazione ufficiale Algolia sul limite: DATO MANCANTE.
- Quora (fonti terze): [Law Insider (frammento ToS)](https://www.lawinsider.com/clause/scraping/_3), [PromptCloud](https://www.promptcloud.com/is-it-legal-to-scrape-quora/).
- Facebook Groups API: [thread sviluppatori Meta](https://developers.facebook.com/community/threads/584177870580474/), [Ayrshare](https://www.ayrshare.com/facebook-removes-groups-api-access-impact-and-implications/), [Make](https://community.make.com/t/due-to-the-deprecation-of-the-facebook-groups-api-we-make-will-be-discontinuing-our-facebook-groups-app/32624.md).
- TikTok Research API: [codebook ufficiale](https://developers.tiktok.com/docs/en/research-api-codebook), [Forklog (caso Maastricht)](https://forklog.com/en/researchers-report-barriers-to-accessing-social-media-data-in-the-eu/).
- Amazon, PA-API senza recensioni: [plugin WordPress (avviso)](https://de.wordpress.org/plugins/wp-json/wp/v2/plugin/15309). Conditions of Use: vedi `docs/04-fonti-trend.md`.
- Trustpilot (fonti terze, con cutoff dichiarato al 2023): [webscraping.ai](https://webscraping.ai/faq/trustpilot-scraping/what-are-the-alternatives-to-scraping-trustpilot-directly).
- SerpApi/DataForSEO: [DataForSEO](https://dataforseo.com/pricing/serp/google-autocomplete-serp-api). Causa Google: link in §1.
- Product Hunt: [producthunt.com/v2/docs](https://www.producthunt.com/v2/docs) (ufficiale).
- Discourse RSS: [meta.discourse.org](https://meta.discourse.org/t/discourse-rss-feeds/264134). Limiti JSON (fonti terze, in conflitto): [Apify](https://apify.com/automation-lab/discourse-scraper).

---

## 3. Copertura realistica

- **Italiano:** RSS di forum e community selezionati a mano (Discourse e forum con feed), commenti YouTube su ricerche in italiano e, quando arriva l'approvazione, Reddit su r/italy, r/Italia e sub tematici. Dal punto di vista quantitativo è una **minoranza** delle conversazioni italiane: quelle su gruppi Facebook, TikTok e WhatsApp restano fuori, e non c'è modo lecito di leggerle.
- **Inglese:** Stack Exchange (DIY, cucina, outdoor, genitori), HN (poco utile per il consumatore), Reddit. Serve come conferma ("il problema esiste anche altrove"), ma il clustering **non fonde IT ed EN** perché non c'è traduzione: un problema bilingue appare come due cluster.
- **Bias** (dalla skill customer-research): Reddit e HN sono tecnici e scettici; chi recensisce o si lamenta è più polarizzato della media. Il segnale serve a **generare ipotesi**, non a misurare il mercato.
- **Conseguenza:** un'opportunità è un'ipotesi da validare con Google Trends/SerpApi e Meta Ad Library (doc 04) e poi con un test reale (landing con prezzo, pre-ordine). Non è una prova di domanda.

---

## 4. Come funziona il modulo (`app/dropship/problems/`)

| File | Ruolo |
|---|---|
| `sources.py` | `DiscussionSource` + `MockDiscussionSource` (source="MOCK", URL `example.invalid`) + `RedditSource`, `StackExchangeSource`, `YouTubeCommentsSource`, `HackerNewsSource`, `RssSource`; `RateLimiter`; `DENIED_DOMAINS`; robots.txt; factory `build_discussion_sources(env)` |
| `text.py` | pulizia HTML (le citazioni `<blockquote>` sono escluse), **redazione** di email, @utente, u/utente, telefoni e link; tokenizzazione IT+EN, stemming a prefisso |
| `extract.py` | pattern IT+EN ("non riesco a", "come faccio a", "qualcuno sa", "odio quando", "si rompe sempre", "c'è un modo per", "how do I", "is there a product", "keeps breaking"…), intensità, intento d'acquisto, risolvibilità fisica, deduplica (copia-incolla e crosspost contano una volta) |
| `cluster.py` | TF-IDF + coseno in puro Python, greedy deterministico |
| `scoring.py` | `ProblemScore` + decisione `OPPORTUNITA` / `DA MONITORARE` / `SKIP` + confidenza `ALTA`/`MEDIA`/`BASSA`/`INSUFFICIENTE` |
| `pipeline.py` | `mine_problems(...)` → `MiningReport`; `format_report` in italiano, con citazioni |

**Punteggio (0–100):** frequenza in post unici, saturata a 20 (25 punti) · intento d'acquisto (20) · risolvibilità con prodotto fisico (15) · intensità (15) · crescita ultimi 30 giorni vs 30 precedenti (15; se mancano le date → DATO MANCANTE e 0 punti, mai stimata) · varietà di fonti (10). **Una sola piattaforma → punteggio ×0,7** e al massimo `DA MONITORARE`.

**Regole di decisione (soglie configurabili da variabili d'ambiente):**
- meno di `DROPSHIP_PROBLEM_MIN_EVIDENCE` (default 5) post unici → **SKIP**;
- risolvibilità fisica sotto `DROPSHIP_PROBLEM_MIN_PHYSICAL` (default 0,4) → **SKIP**. Copre software, burocrazia e problemi medici (farmaci e dispositivi medici sono esclusi a monte);
- meno di `DROPSHIP_PROBLEM_MIN_SOURCES` (default 2) piattaforme → **DA MONITORARE**;
- punteggio sotto `DROPSHIP_PROBLEM_MIN_SCORE` (default 55) → **DA MONITORARE**;
- altrimenti → **OPPORTUNITA**.

Le altre soglie configurabili sono `DROPSHIP_PROBLEM_CLUSTER_SIMILARITY` (0,2) e `DROPSHIP_PROBLEM_GROWTH_WINDOW_DAYS` (30). Valori assurdi fanno fallire l'avvio (`ConfigError`).

**Evidenze:** ogni citazione è (fonte, piattaforma, URL, data, estratto di al massimo 200 caratteri, `retain_until`) ed è **sempre** presa da un post ricevuto davvero. Se la data manca, compare "DATO MANCANTE". Le citazioni sono scelte prima una per piattaforma, poi da post diversi. Le opportunità costruite su dati MOCK sono marcate `[MOCK]` e non vanno usate per decidere.

**Privacy:** `Post` **non ha un campo autore**: gli adapter non leggono mai `author`, `owner`, `authorDisplayName` o `authorChannelUrl` (c'è un test per ogni adapter). Il testo è troncato a 1.500 caratteri, le citazioni a 200. `retain_until` ricorda gli obblighi di cancellazione: Reddit 2 giorni, YouTube 30 giorni dalla raccolta. Base giuridica: legittimo interesse con minimizzazione. **Va documentato nel registro dei trattamenti** (compito umano).

**Sicurezza:** solo HTTPS; chiavi incapsulate in `Secret` (mai nei `repr`, nei log o negli errori); messaggi d'errore senza URL o query; XML con DTD/ENTITY rifiutato (XXE/billion laughs); decompressione gzip limitata a 10 MB; feed limitati a 2 MB; testo di terzi trattato come **dato non fidato** (non viene mai eseguito né interpretato come istruzioni).

**Correttezza verso i siti:** User-Agent `dropship-problem-miner/0.1 (+DROPSHIP_CONTACT)`. Per Reddit il formato è quello richiesto da loro, tramite `REDDIT_USER_AGENT`. Intervallo minimo per fonte: Reddit 1 s, Stack Exchange 0,5 s + `backoff`, YouTube 0,5 s + budget quota, HN 1 s, RSS 5 s per dominio o il `Crawl-delay`. Se robots.txt risponde 401/403/5xx, il feed non viene letto.

---

## 5. Chiavi e accessi necessari

| Variabile | Serve per | Come ottenerla |
|---|---|---|
| `DROPSHIP_CONTACT` | User-Agent identificabile (email o URL) | da decidere (es. email del progetto) |
| `YOUTUBE_API_KEY` (+ `YOUTUBE_DAILY_QUOTA`) | commenti YouTube | Google Cloud Console → abilitare YouTube Data API v3 → chiave API |
| `STACKEXCHANGE_KEY` (opzionale; oppure `DROPSHIP_ENABLE_STACKEXCHANGE=1` senza chiave, 300 req/giorno) (+ `STACKEXCHANGE_SITES`) | Stack Exchange | registrare un'app su stackapps.com |
| `DROPSHIP_ENABLE_HN=1` | Hacker News | nessuna chiave |
| `DROPSHIP_PROBLEM_RSS_FEEDS` (lista separata da virgole, HTTPS) | forum/community IT | **verifica manuale dei termini** di ogni sito prima di aggiungerlo |
| `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`, `REDDIT_SUBREDDITS`, `REDDIT_API_APPROVED=1` | Reddit | creare l'app su reddit.com/prefs/apps, **chiedere l'approvazione** (Responsible Builder Policy) e, per l'uso commerciale, un **accordo** con Reddit. Senza questi passaggi, lasciare `REDDIT_API_APPROVED` non impostato |
| `DROPSHIP_FORCE_MOCK=1` | forza i dati MOCK | — |

Senza nessuna variabile, il modulo usa **solo MOCK** e lo dichiara (`describe_discussion_sources`).

---

## 6. Cosa resta da fare (onestamente)

- Leggere i **termini ufficiali** di Reddit, Stack Exchange e Algolia (qui il fetch era bloccato) e confermare i limiti.
- Compilare la **lista dei feed IT ammessi**, sito per sito, con data della verifica dei ToS. Per HDblog, Alfemminile e i forum delle testate i feed e i ToS sono DATO MANCANTE.
- **Traduzione IT↔EN** dei token per fondere i cluster bilingui. Senza, l'evidenza inglese non rafforza quella italiana.
- Le euristiche lessicali (intensità, intento, risolvibilità fisica) sono **liste di parole**: vanno tarate su un campione etichettato a mano. Una revisione umana delle opportunità resta obbligatoria.
- **Persistenza** con cancellazione automatica allo scadere di `retain_until`. Oggi il modulo non salva niente su disco: se in futuro lo farà, la cancellazione va implementata.
