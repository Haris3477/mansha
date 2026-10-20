# Paid models remove limits; tariffs hold

The cheapest fix for Mansha's budget problem is a small paid tier, not a model change. For the `judge` chain, the best fit is Groq's paid Developer plan on the same `openai/gpt-oss-120b`. It raises the per-request ceiling from **8K to 250K TPM** and costs **$0.15 / $0.60 per 1M tokens**. Groq contractually does not train on API data and offers self-serve **Zero Data Retention (ZDR)**. Cerebras's `gpt-oss-120b` is a strong second judge with its own budget: **1M tokens/day free**. For the `long` chain, the lowest-risk addition is paid **Gemini 3.8 Flash**: same family, same prompts, **$0.75 / $3.75 per 1M** through 2026. AI Studio's paid tier does not train on prompts but still logs them "for a limited period". True ZDR needs OpenRouter with ZDR enforced, or Vertex. Money does not decide this: a full paid pipeline run costs about **$0.02–$0.07**, and a 20-case evaluation about **$0.40–$1.40**. On the data side, Notification **15/2026-Customs** amends 45/2025 only for **Chapter 71 precious metals**. No 2026 notification and nothing in the Finance Act 2026 annexures changes the MFN rate or 8-digit code of any of Mansha's 14 lines. Two items are still unconfirmed: the CBIC tariff's current "as on" date and the file number of **Instruction 28/2022-Customs**. Also, **none of the 8 non-government source URLs could be swapped for an official copy from here**, because cbic.gov.in and egazette.gov.in block automated access. A short browser to-do list (end of report) closes these by hand.

## Recommendations at a glance (Haris decides)

These follow the team's plan: **add** a paid model as one more entry in each chain, keep the free models as fallbacks, and keep the code-only fallback.

| # | Recommendation | Why | Trade-off | Gaps |
|---|---|---|---|---|
| 1 | Add Cerebras `gpt-oss-120b` to `auto:judge`, after Groq (free, today) | Same weights as today's judge; separate 1M tokens/day budget; ~3,000 tok/s | Free tier is 5 RPM and may be a trial only; no explicit no-training clause; re-run judge tests (fp16 serving) | G11, G17, G31 |
| 2 | Upgrade Groq to Developer, turn on ZDR, set a $5–10 spend limit | Removes the 8K per-request refusal and the split-review workaround; cleanest data terms (no training by contract + ZDR) | Card on file. Limits are per organization, so Intake's Groq calls likely become billed too (inference). Developer TPD not published | G11, G18, G31 |
| 3 | Add paid Gemini 3.8 Flash first in `auto:long` | Lowest prompt-migration risk; paid tier is not used for training | Logged for an unstated "limited period"; price doubles on 1 Jan 2027 | G16, G17, G18 |
| 3b | If "zero retention" must be claimed for the long chain: route Gemini 3.8 Flash through OpenRouter with ZDR enforced | Documented ZDR path without a sales contract | 10% higher price + 5.5% credit fee; needs OpenRouter credits | G18 |
| 4 | Keep the 14 tariff lines as they are; update the citation wording | No 2026 change found | 7 of the 14 lines are "unchanged on evidence read", not checked line by line in the Finance Act Schedules | G22 |
| 5 | Mark the 8 non-government URLs PRIMARY-COPY until a browser check | Official hosts block automated fetching | Judges see non-government links until the check is done | G21 |

## A $5 Groq upgrade ends the judge-chain squeeze

Today's judge runs into two walls. First, the **8,000 TPM per-request cap** counts prompt plus `max_tokens`. Second, the **200,000 tokens/day** budget runs out. Measured judge calls use **3,700–5,400 input and 1,000–1,600 output tokens**, with 1–6 judge calls per run. A typical run is ~22,000 tokens, so a 20-case evaluation needs ~440,000 tokens (~860,000 worst case). That is **more than twice Groq's free daily budget**, which matches what the team saw (G31).

On the Developer plan, `openai/gpt-oss-120b` gets **1K RPM and 250K TPM** at **$0.15 input, $0.075 cached input and $0.60 output per 1M**. It has a 131,072-token context and runs at about 500 tok/s ([Groq Models](https://console.groq.com/docs/models); [model page](https://console.groq.com/docs/model/openai/gpt-oss-120b)). Upgrading needs only a payment method. It takes effect immediately, with **no minimum spend** and monthly billing in arrears; early invoices come at $1/$10/$100 lifetime-usage thresholds. Automated spend limits are available ([Groq Billing FAQs](https://console.groq.com/docs/billing-faqs)). Rate limits apply **per organization**, and cached tokens do not count against them ([Groq Rate Limits](https://console.groq.com/docs/rate-limits)). One gap remains: Groq's docs page did not render the Developer-plan **RPD and TPD** for this model, so the daily cap must be read from the org's Limits page after upgrading. Flex processing gives "10x higher rate limits" at the same price, but it fails fast with HTTP 498 when capacity is full ([Groq Flex](https://console.groq.com/docs/flex-processing)). Batch is not useful: its window is 24 hours or more, and ZDR disables it.

Groq also has the cleanest data story (G18). The Services Agreement says "Groq is not permitted to use Inputs or Outputs for training" ([Services Agreement](https://console.groq.com/docs/legal/services-agreement), last modified 22 June 2026). By default, Groq may log inputs and outputs for **up to 30 days** for abuse and reliability checks. Any customer can switch that off with **ZDR in Data Controls** ([Groq Your Data](https://console.groq.com/docs/your-data)). The docs say "all customers", so ZDR can probably be turned on today, before any upgrade; check this in Data Controls. Retained data sits in **US GCP buckets**. Groq does not document where requests are processed, and UAE PDPL transfer rules were not researched. Mansha's rule of sending only synthetic data and counts/percentages to the LLMs sidesteps both questions for the hackathon.

Cerebras is the natural second entry in `auto:judge`. It serves the same `gpt-oss-120b` at about **3,000 tok/s** for **$0.35 / $0.75 per 1M** ([Cerebras model page](https://inference-docs.cerebras.ai/models/openai-oss)). The free tier allows **1M tokens/day**, 30K uncached TPM and only **5 RPM**. Pay-as-you-go gives 1K RPM, 1M uncached TPM and no daily cap ([Cerebras Rate Limits](https://inference-docs.cerebras.ai/support/rate-limits)). Two caveats apply. The pricing page now describes a one-time **$5 credit that expires after 30 days**, so free access may be a trial rather than permanent ([Cerebras Pricing](https://www.cerebras.ai/pricing)). And Cerebras states non-retention of prompts and outputs ([support article](https://cerebras-inference.help.usepylon.com/articles/1811589793-does-cerebras-retain-my-data); [Privacy Policy](https://www.cerebras.ai/privacy-policy)), but it has **no explicit contractual no-training clause**. Cerebras serves fp16 and defaults to medium reasoning, so re-run the judge test set before trusting its verdicts.

OpenRouter lists more than 20 hosts for `gpt-oss-120b`. Only **Near AI (fp4) and Venice (int4)**, both $0.03 / $0.15, showed up in the visible part of its ZDR list, and that list was truncated ([OpenRouter endpoints](https://openrouter.ai/api/v1/models/openai/gpt-oss-120b/endpoints); [ZDR list](https://openrouter.ai/api/v1/endpoints/zdr)). Venice's int4 quantization may change judge behaviour. Vertex showed **7.78% one-day uptime** through OpenRouter on 17 Oct.

| Judge option | Price per 1M (in / out) | Limits | Speed | Data terms | Run, typical–worst | 20-case eval, typical–worst |
|---|---|---|---|---|---|---|
| Groq free (today) | $0 | 8K TPM per request, 200K TPD, 30 RPM | ~500 tok/s | Same no-training contract; up to 30-day logs unless ZDR is on | n/a | Exceeds daily budget |
| **Groq Developer + ZDR** | $0.15 / $0.60 | 250K TPM, 1K RPM; TPD unpublished | ~500 tok/s | No training (contract); ZDR self-serve | $0.003–$0.011 | $0.05–$0.22 |
| Cerebras free | $0 | 1M TPD, 5 RPM, 30K uncached TPM | ~3,000 tok/s | Non-retention stated; no training clause found | $0 | Fits 1M TPD (worst ~860K) |
| Cerebras PayGo | $0.35 / $0.75 | 1K RPM, no daily cap | ~3,000 tok/s | Same | $0.010–$0.019 | $0.19–$0.38 |
| Near AI / Venice via OpenRouter ZDR | $0.03 / $0.15 + 5.5% fee | No platform cap | Unknown | ZDR enforced | ~$0.002 worst | ~$0.05 worst |

Costs include one Intake call (700 / 270 tokens) plus 2–6 judge calls, with no cache discount. The arithmetic is in the research notes and uses the cited prices.

## Gemini 3.8 Flash is the low-risk long-chain add

The `long` chain carries most of the tokens and most of the latency. Measured Researcher calls use **~7,700–8,600 input tokens**. Output is **1,400 tokens on Gemini and 5,500 on the reasoning model**. Builder calls use ~1,900 in and 350–4,900 out. Today the chain runs on free Gemini Flash plus a slow free preview model. That raises two problems. On speed (G16), the slow fallback, not Gemini, threatens the 60-second goal. On data (G18), the Gemini **free tier lets Google use prompts to improve products, and human reviewers may read them** ([Gemini API terms](https://ai.google.dev/gemini-api/terms)).

Paid Gemini fixes the data point with almost no code change. Under the paid terms, "Google doesn't use your prompts" to improve products. But Google still "logs prompts and responses for a limited period of time" for abuse and legal reasons, the period is not stated, and data may be cached in any country ([Gemini API terms](https://ai.google.dev/gemini-api/terms), updated 28 Apr 2026). `gemini-3.8-flash` costs **$0.75 / $3.75 per 1M through 31 Dec 2026**, then **$1.50 / $7.50 from 1 Jan 2027**. `gemini-3.6-flash` has the same price. `gemini-3.5-flash-lite` costs $0.30 / $2.50 ([Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)). Tier 1 needs only a billing account. It has a $250 billing cap and a $10 per 10 minutes spend limit; per-model RPM/TPM/RPD are shown only in AI Studio ([Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)). New Google Cloud customers get a **$300 credit** ([Google Cloud free](https://cloud.google.com/free)). It is not confirmed that this credit covers AI Studio billing.

The model page lists `gemini-3.8-flash` and `gemini-3.6-flash` as stable, and 3.5 only as Flash-Lite ([Gemini models](https://ai.google.dev/gemini-api/docs/models)). The router log shows calls **successfully served by `gemini-3.5-flash` and `gemini-3.7-flash` on 16–17 Oct**, so those IDs work today. Treat this as a **deprecation check**, not a mismatch.

For a real "zero retention" claim, the documented self-serve route is **OpenRouter with ZDR enforced**. OpenRouter does not store prompts unless you opt in. ZDR can be forced account-wide or per request with `provider.zdr: true`. Under ZDR, AI Studio endpoints are dropped and Vertex remains ([OpenRouter ZDR](https://openrouter.ai/docs/features/zdr); [privacy and logging](https://openrouter.ai/docs/features/privacy-and-logging)). Its ZDR list includes `google/gemini-3.8-flash` and `google/gemini-3.7-flash` at **$0.825 / $4.125**. OpenRouter passes model prices through without markup, but charges a **5.5% fee on credit purchases** ([OpenRouter FAQ](https://openrouter.ai/docs/faq)). Vertex directly also supports ZDR, but the abuse-monitoring exception is by request ([Google Cloud ZDR](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/zero-data-retention)).

Cheaper models from other families exist, and each costs a prompt re-test. **Groq `gpt-oss-120b`** costs $0.15 / $0.60, runs at ~500 tok/s, supports strict JSON schema and has self-serve ZDR ([Groq structured outputs](https://console.groq.com/docs/structured-outputs)). At ~500 tok/s, it would write 5,500 tokens in about 11 s. But putting the Researcher on the same model as the judge weakens QA independence; that is an inference, not tested. **OpenAI `gpt-6-luna`** costs $0.10 / $0.50, with structured outputs and no training by default. It keeps abuse logs for 30 days, and ZDR needs sales approval ([OpenAI pricing](https://developers.openai.com/api/docs/pricing); [your data](https://developers.openai.com/api/docs/guides/your-data)). At Max reasoning, Artificial Analysis measured a **97 s time to first token**, against 24 s for Gemini 3.8 Flash at High ([Artificial Analysis](https://artificialanalysis.ai/models/comparisons/gpt-6-luna-vs-gemini-3-8-flash)). It would need low effort to fit 60 s. **Claude Haiku 5.5** costs $0.10 / $0.50 ([Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing)). Anthropic's OpenAI-compatible endpoint ignores `response_format` and is "not production-ready" ([Anthropic OpenAI SDK](https://platform.claude.com/docs/en/api/openai-sdk)), so the workable route is OpenRouter ZDR via Vertex or Bedrock.

| Long-chain option | Price per 1M (in / out) | Speed | Data terms | Run, best–worst | 20-case eval, best–worst | Fit |
|---|---|---|---|---|---|---|
| **Gemini 3.8 Flash, AI Studio paid** | $0.75 / $3.75 (2026) | 147 tok/s, 24 s TTFT at High | No training; logged for an unstated "limited period" | $0.017–$0.059 | $0.34–$1.18 | Same family; lowest risk |
| Same, from 1 Jan 2027 | $1.50 / $7.50 | same | same | $0.034–$0.118 | $0.69–$2.37 | Price doubles |
| Gemini 3.8 Flash via OpenRouter ZDR | $0.825 / $4.125 | not measured | ZDR enforced | $0.019–$0.065 | $0.38–$1.30 + 5.5% | Best data claim for Gemini |
| Gemini 3.5 Flash-Lite, paid | $0.30 / $2.50 | not measured | as AI Studio paid | $0.009–$0.036 | $0.19–$0.71 | Weaker model; re-test |
| Groq gpt-oss-120b + ZDR | $0.15 / $0.60 | ~500 tok/s | No training; ZDR | $0.003–$0.010 | $0.06–$0.20 | Fast; different family; same model as judge |
| gpt-6-luna | $0.10 / $0.50 | 120 tok/s; 97 s TTFT at Max | No training; 30-day logs; ZDR by approval | $0.002–$0.008 | $0.05–$0.16 | Needs low effort for speed |
| Claude Haiku 5.5 via OpenRouter ZDR | $0.10–$0.11 / $0.50–$0.55 | not measured | ZDR via Vertex/Bedrock | ~$0.002–$0.008 | ~$0.05–$0.16 | Different family; re-test |

Best case = 1 Researcher (8,500 / 1,500) + 1 Builder (1,900 / 1,000). Worst case = 2 Researcher rounds at 5,500 output + 1 Builder. The measured Builder maximum of 4,900 output adds up to ~$0.015 per run on Gemini 3.8 Flash. Speed figures are third-party or estimated, not measured on Mansha.

Combining recommendations 2 and 3 (Groq judge + Gemini 3.8 Flash long chain) gives **~$0.02–$0.07 per run** and **~$0.40–$1.40 per 20-case evaluation** at 2026 prices. A $10 budget covers several full evaluation rounds.

## None of the 14 tariff lines moved in 2026

Notification **15/2026-Customs** is dated **12 May 2026** (G.S.R. 358(E), F. No. 354/04/2026-TRU) and took effect on 13 May. It amends the effective-rate notification 45/2025-Customs only in the **Chapter 71 precious-metal block**. Serial numbers 192–197 and 203 go from 5% to 10%. A new S. No. 200A covers spent catalyst/ash (7112) until 31 Mar 2027, and S. No. 202 is substituted ([15/2026 copy](https://www.caalley.com/cus26/cst-15-2026.pdf)). The G.S.R. number comes from the footnote of 25/2026 ([25/2026 copy](https://www.caalley.com/cus26/cst-25-2026.pdf)). Mansha's earlier note ("15/2026 amends 45/2025, not read") was correct. What is new is the content: precious metals only.

Two related findings. The Finance Act 2026 code realignment was **14/2026-Customs** (30 Apr 2026, G.S.R. 330(E)). It amends the CEPA notification 22/2022 Table I, not 45/2025, and **none of the 14 codes** appears in it. A corrigendum exists and was not read ([TaxGuru full text](https://taxguru.in/?p=1041189)). A same-day companion, **18/2026-Customs**, changes CEPA Table III S. No. 12, a precious-metals quota line ([TaxGuru](https://taxguru.in/?p=1043189)). That answers the open question of whether 18/2026 supersedes N09's tables for our lines: it does not, though this rests on aggregator copies. Two other notifications share the number 15/2026 (an anti-dumping one and an N.T. baggage one). Cite the full name "15/2026-Customs".

The official Budget 2026-27 annexures say **"No Change" for Chapters 16–19, 32, 75–77 and 91–94**. The changes in Chapters 33, 39, 84 and 85 touch other codes (3302, 3923 29 90, 8401/8415/8421, and 8501 10 20 / 8504 31 00 / 8516 for microwave ovens). The First Schedule changes took effect on 1 May 2026 ([indiabudget.gov.in annexures](https://www.indiabudget.gov.in/doc/cen/dojstru1.pdf)). The Chapter 73 changes (7305/7306/7318/7325) come only from a reproduction of the CBIC letter ([TaxGuru](https://taxguru.in/income-tax/budget-2026-key-customs-excise-gst-legislative-duty-changes.html)). The 2026 amendment chain of 45/2025 is unbroken: **02 → 06 → 15 → 25 → 31/2026**, each footnote naming the previous one. None of them touches our lines ([02/2026, official](https://www.indiabudget.gov.in/doc/cen/cus0226.pdf); [31/2026 copy](https://www.caalley.com/cus26/cst-31-2026.pdf)).

| Line | Tariff / effective BCD % | Status |
|---|---|---|
| 19053100, 19059090 | 30 / 30 | Unchanged (Ch 16–19 "No Change", official) |
| 76101000 | 10 / 10 | Unchanged (Ch 75–77, official) |
| 76151030 | 20 / 20 | Unchanged (Ch 75–77, official) |
| 76041010 | 7.5 / 7.5 | Unchanged (Ch 75–77, official) |
| 94036000 | 20 / 20 | Unchanged (Ch 91–94, official) |
| 32091010 | 10 / 10 | Unchanged (Ch 32, official) |
| 73089090 | 15 / 10 | Unchanged on evidence read |
| 39239090 | 15 / 15 | Unchanged on evidence read (only 3923 29 90 split) |
| 33030090, 33049990 | 20 / 20 | Unchanged on evidence read (Ch 33 change is 3302 only) |
| 85044030 | 20 / 20 | Unchanged on evidence read |
| 85171300 | 20 / 20 | Unchanged on evidence read |
| 84713010 | 0 / 0 | Unchanged on evidence read |

"On evidence read" means the line is absent from every annexure and notification checked. The Finance Act's Fourth and Fifth Schedules were not read line by line, so these lines are low-risk but not proven. Amendments after 31/2026 (23 Sep 2026) were not checked.

The CBIC tariff Mansha cites is "as on 30.06.2024". That predates two Finance Acts, and no newer official edition was confirmed. Until it is, cite it as "CBIC tariff as on 30.06.2024, read with the Finance Acts 2025/2026 and 45/2025 as amended to 31/2026".

## Instruction 28/2022 and the official URLs need a browser

**Instruction 28/2022-Customs** is dated **27 Oct 2022**. Its content is known only from LiveLaw's quotes. An e-CoO issued electronically by the UAE Issuing Authority is valid for CEPA preference if it is in the prescribed format, bears the electronic seal and signature, and meets 39/2022-Customs (N.T.). The importer uploads it to e-Sanchit and enters its reference number, date and origin criterion in the bill of entry. A printed copy is defaced at out-of-charge. The system blocks reuse of one CoO number across bills of entry, and doubtful cases go to the FTA Cell ([LiveLaw](https://www.livelaw.in/amp/news-updates/cbic-acceptance-e-coo-issued-india-uae-cepa-electronic-certificate-of-origin-212723); [Taxmann](https://taxmann.com/post/blog/clarification-on-acceptance-of-e-coo-issued-under-india-uae-cepa-instruction)). The **file number, addressees and signatory were not found**. The LiveLaw-hosted PDF (`cs-ins-28-2022`) is an image scan; OCR would likely recover them.

None of the 8 non-government sources (R39, R39-G, N22, N09, A2A, N45-2025, CTA-2017, CBIC-INSTR-28) could be confirmed on an official host. CBIC's old static paths and e-Gazette refuse automated fetching. The new taxinformation.cbic.gov.in portal loads only as an empty JavaScript shell. The blocks are on fetchers, not on the documents. Two partial wins:

- The **moet.gov.ae agreement PDF** is a confirmed official copy of the CEPA main text, including Chapter 3 (Rules of Origin). It does not contain the annex bodies, so it is a companion to R39, not a replacement for A2A or R39-G ([moet.gov.ae PDF](https://www.moet.gov.ae/documents/20121/1347101/Final+Agreement_UAE+India+CEPA.pdf)).
- The **commerce.gov.in India-UAE CEPA page** lists Annex 2A (India's tariff schedule) and Annex 3B (Product Specific Rules), dated 27 Mar 2022, but the link targets could not be captured ([commerce.gov.in](https://www.commerce.gov.in/international-trade/trade-agreements/comprehensive-economic-partnership-agreement-between-the-government-of-the-republic-of-india-and-the-government-of-the-united-arab-emirates-uae/)).

Separately, indiabudget.gov.in is an official host that already serves 02/2026-Customs and the Budget annexures. It can be cited for those directly.

### Browser to-do list (about 20 minutes)

1. **Groq** (after upgrading): console.groq.com/settings/limits. Record the RPD/TPD for `openai/gpt-oss-120b` and whether TPM is split into input and output caps. Then console.groq.com/settings/data-controls: turn on ZDR and take a screenshot for the pitch.
2. **Cerebras**: Cloud Console, Limits. Check whether the free tier is permanent or the $5 / 30-day trial.
3. **AI Studio**: record the Tier 1 RPM/TPM/RPD for `gemini-3.8-flash`, and any deprecation date for `gemini-3.5-flash` and `gemini-3.7-flash`.
4. **OpenRouter**: open https://openrouter.ai/api/v1/endpoints/zdr and search for `gpt-oss-120b`, `gemini-3.8-flash` and `gpt-6-luna` to get the full ZDR list.
5. **CBIC tariff**: taxinformation.cbic.gov.in, Customs, Tariff. Record the current "as on" date.
6. **CBIC Instruction**: taxinformation.cbic.gov.in, Customs, Instructions, 2022, No. 28. Copy the PDF URL, F. No. and signatory.
7. **CBIC notifications**: copy the official PDF URLs for 39/2022-Customs (N.T.) (R39 + Annexure-B), 22/2022-Customs (N22), 09/2026-Customs (N09), 45/2025-Customs (N45-2025), 15/2026-Customs and 18/2026-Customs.
8. **e-Gazette** (egazette.gov.in search by G.S.R.): 328(E) 2022, 238(E) 2026, 781(E) 2025, 358(E) 2026.
9. **commerce.gov.in** India-UAE CEPA page: right-click "Annex 2A" and "Annex 3B" and copy the PDF links (for A2A and R39-G).
10. **indiacode.nic.in**: search "Taxation Laws (Amendment) Act, 2017" (CTA-2017).
11. *Optional*: in the Finance Act 2026, Fourth Schedule, confirm that 3923 90 90, 7308 90 90, 3303/3304, 8471 30 10, 8504 40 30 and 8517 13 00 are not amended.

## Conclusion

Mansha's limits come from free-tier quotas, not from model quality, and the cost of removing them is tiny: under $2 for a full 20-case evaluation. The real choices are about **evidence for judges**. Groq with ZDR gives a contract-backed "no training, no retention" line for the judge. For the long chain, Haris has to pick between paid Gemini (same prompts, but limited-period logging) and Gemini via OpenRouter ZDR (a stronger claim, at slightly higher cost). Either way, free fallbacks stay in the chain, and they are acceptable only because Mansha sends them synthetic data alone. That rule is worth stating in the pitch. On the data side, 2026 changed nothing for the 14 lines. The remaining work is citation hygiene, not re-research: almost every open data gap now closes with a browser and copy-paste.

## Gaps still open

| Gap | Why still open | How to close |
|---|---|---|
| G11 QA model/budget | Options identified, none applied yet; Developer TPD unknown | Steps 1–2 of the to-do list; re-run the judge test set on Groq Developer and on Cerebras |
| G16 Speed < 60 s | No measured timings for paid models on Mansha's prompts; Gemini 3.8 Flash TTFT at High is 24 s | Time 3–5 runs per candidate from `runs/` logs; set a low thinking level |
| G17 Reliability | Cerebras free may be trial-only (5 RPM); Groq flex returns 498; Vertex via OpenRouter unhealthy on 17 Oct | Add Cerebras and paid Gemini as extra chain entries; keep the code-only fallback; handle 498 in the router's retry logic |
| G18 Data terms | AI Studio paid log period not stated; Cerebras has no training clause; Groq processing region and UAE PDPL not researched | Use Groq ZDR + OpenRouter ZDR for the "zero retention" claim; keep the synthetic-data-only rule; read Groq's DPA if needed |
| G21 Non-government URLs | All 8 unconfirmed; official hosts block automated fetching | To-do steps 6–10; add the moet.gov.ae agreement PDF and the indiabudget.gov.in links now |
| G22 Open data checks | CBIC tariff "as on" date, Instruction 28/2022 F. No., Finance Act Schedules line by line, post-31/2026 amendments, 14/2026 corrigendum | To-do steps 5–8 and 11; re-check 45/2025 amendments after 23 Sep 2026 |
| G31 Groq daily budget | One 20-case eval (~440K tokens) is more than twice the 200K free TPD | Groq Developer (step 2) or Cerebras as the second judge (step 1) |
| Credits (no ID) | Whether the $300 Google Cloud credit covers AI Studio is unverified; hackathon credits not checked | Check in GCP Billing; ask the championship organisers |
