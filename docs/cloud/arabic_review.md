# Arabic wording for review (N15, the Arabic task)

Written by Claude on 28 Oct 2026, branch `claude/arabic-gap-n15-yfk0w0`. Haris's plan (28 Oct): push only the Arabic we can confirm. New Arabic sentences wait here until Haris and a friend who reads Arabic have reviewed them. A wording fix later is a text edit plus the offline tests. These texts are printed by code and never sent to a model, so a fix needs no live sitting.

For each item, tick it, or write the corrected Arabic next to it.

## Part 1: in the code now (step 2). Haris checks these.

### Authority names (`AUTHORITY_TEXT`, `mansha/document_builder.py`)
These fill the line "الجهة المختصة: …" under each checklist step. The key is the KB record's `actor`.

**Ministries.** Each is the ministry's official Arabic name. Check it against the Arabic version of the ministry's own website.

| KB actor | Arabic | Check against |
|---|---|---|
| the Ministry of Economy and Tourism | وزارة الاقتصاد والسياحة | moet.gov.ae (Arabic); also used in the live step text of `P-MOET-FACTORY-REG` |
| the Ministry of Foreign Trade | وزارة التجارة الخارجية | trade.gov.ae (Arabic) |

- [ ] وزارة الاقتصاد والسياحة
- [ ] وزارة التجارة الخارجية

**Role words.** These are plain Arabic.

| KB actor | Arabic | Note |
|---|---|---|
| the exporter | المُصدِّر | with diacritics, because "المصدر" without them reads as "the source" |
| the Indian importer | المستورد الهندي | already in the live step text of `P-IN-IMPORTER` |
| the issuing authority | جهة الإصدار | already in the live step text of `P-AGR-3.17-APPLICATION` |
| the competent authority | السلطة المختصة | not "الجهة المختصة", which is the line's own label |

- [ ] المُصدِّر
- [ ] المستورد الهندي
- [ ] جهة الإصدار
- [ ] السلطة المختصة

### Notice when the Arabic prose falls back to English (`FALLBACK_NOTICE`)
This appears when the Builder's Arabic still fails the script check after its one retry. The report then uses the English code-only prose, and this line comes first:

> تنبيه: تعذّر إعداد شرح هذا التقرير باللغة العربية بجودة كافية، لذلك يظهر الشرح باللغة الإنجليزية.

It means: "Note: the explanation in this report could not be prepared in Arabic at sufficient quality, so it is shown in English."

- [ ] Notice OK

## Part 2: drafts, IN THE CODE since 29 Oct (before the review, Haris: option A). For Haris and his friend.
Code prints these in Arabic reports (`mansha/document_builder.py`: `SAVING_AR`, `MFN_SPLIT_AR`, `NOTE_AR_DRAFTS`, `VERDICT_TEXT_AR`, `ORIGIN_TEXT_AR`, `FALLBACK_AR`); the reader's corrections replace them as text edits. `FALLBACK_NOTICE` was removed: the code-only prose is Arabic now, with English KB details in brackets (F-a). The review PDF (`docs/arabic_review/`) numbers these as items 10-35 and 87-92.

### Saving cell in the duty table (`saving_text`)

| English | Arabic draft |
|---|---|
| (only if the product qualifies) | (فقط إذا كان المنتج مؤهلًا) |
| none, because the product does not qualify | لا يوجد، لأن المنتج غير مؤهل |
| none, because the tariff line is excluded from CEPA preference | لا يوجد، لأن البند الجمركي مستثنى من التفضيل بموجب الاتفاقية |
| cannot be estimated without the shipment value | لا يمكن تقديره دون قيمة الشحنة |
| not in Mansha's sources | غير موجود في مصادر منشأ |

### MFN cell in the duty table (seen in 015311 r2 and 022326 r1)

| English | Arabic draft |
|---|---|
| tariff {t}, effective {e} | النسبة في جدول التعريفة {t}، والنسبة الفعلية {e} |

### Notes printed word for word (N15 showed 5 in English)
Today these are the Researcher's English wording of each tool or KB note. With a reviewed Arabic text, code would print the tool's own note in Arabic instead.

1. **The '+' rule** (KB `psr.metadata.interpretations`): "'+' in a rule is read as 'and' (both tests must pass). The agreement does not define '+', so this is Mansha's interpretation."
   - Arabic draft: علامة '+' في القاعدة تُقرأ بمعنى 'و' (يجب اجتياز الاختبارين معًا). لا تعرّف الاتفاقية علامة '+'، لذلك هذا تفسير منشأ.
2. **Estimate basis** (`mansha/tools/duty_estimate.py`): "Estimate on the shipment value given. India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Shown in the shipment's own currency; never converted."
   - Arabic draft: تقدير مبني على قيمة الشحنة المذكورة. تحتسب الهند الرسوم على القيمة الخاضعة للتقييم (CIF) عند الاستيراد، لذلك ستختلف المبالغ الفعلية. يُعرض المبلغ بعملة الشحنة نفسها، دون تحويل.
3. **What the CEPA rate reduces** (KB `tariff.metadata.duty_scope`): "CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, the Social Welfare Surcharge (SWS) and any anti-dumping or safeguard duty still apply."
   - Arabic draft: تخفّض أسعار الاتفاقية الرسوم الجمركية الأساسية (BCD) فقط. وتبقى مستحقة ضريبة السلع والخدمات المتكاملة (IGST)، ورسم التعويض عن ضريبة السلع والخدمات، ورسم الرعاية الاجتماعية الإضافي (SWS)، وأي رسوم لمكافحة الإغراق أو رسوم وقائية.
4. **When the CEPA rate applies** (`duty_estimate.py`): "The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented."
   - Arabic draft: لا يُطبَّق سعر الاتفاقية إلا إذا استوفى المنتج قواعد المنشأ وقُدِّمت شهادة منشأ سارية.
5. **The issuer** (KB `P-UAE-ISSUER` note): "No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically: its service page covers preferential certificates in general, and the India-specific page is still on moet.gov.ae."
   - Arabic draft: لا تذكر أي صفحة رسمية اطّلعنا عليها أن وزارة التجارة الخارجية هي الجهة المصدرة لشهادة المنشأ الخاصة باتفاقية الهند تحديدًا: فصفحة خدمتها تتناول شهادات المنشأ التفضيلية بشكل عام، ولا تزال الصفحة الخاصة بالهند منشورة على موقع moet.gov.ae.

Other tool notes can reach an Arabic report in other cases, and they have no draft yet: excluded line, Table II and Table III lines, no usable value, Indian inputs, and the origin tool's check notes. They are listed so they're not forgotten.

### Code-only prose (`fallback_prose`, `VERDICT_TEXT`, `ORIGIN_TEXT`)

| English | Arabic draft |
|---|---|
| ELIGIBLE: the product meets the rule of origin, so the CEPA rate can be claimed | المنتج يستوفي قاعدة المنشأ، لذلك يمكن المطالبة بسعر الاتفاقية |
| NOT_ELIGIBLE: the product does not meet the rule of origin, so the normal (MFN) rate applies | المنتج لا يستوفي قاعدة المنشأ، لذلك يُطبَّق السعر العادي (MFN) |
| NEEDS_MORE_DATA: Mansha cannot confirm the result yet, because information is missing | لا يمكن لمنشأ تأكيد النتيجة بعد، لأن بعض المعلومات ناقصة |
| NO_PREFERENCE: this tariff line is excluded from CEPA preference, so the normal (MFN) rate applies whatever the product's origin | هذا البند الجمركي مستثنى من التفضيل بموجب الاتفاقية، لذلك يُطبَّق السعر العادي (MFN) أيًّا كان منشأ المنتج |
| gap: Mansha's sources do not cover this product well enough to give a result | مصادر منشأ لا تغطي هذا المنتج بما يكفي لإعطاء نتيجة |
| origin QUALIFIES: meets the rule of origin | يستوفي قاعدة المنشأ |
| origin DOES_NOT_QUALIFY: does not meet the rule of origin | لا يستوفي قاعدة المنشأ |
| origin NEEDS_MORE_DATA: cannot be checked yet, because information is missing | لا يمكن فحصه بعد، لأن بعض المعلومات ناقصة |
| origin NOT_APPLICABLE: is not checked, because the line is excluded from CEPA preference | لا يُفحص، لأن البند مستثنى من التفضيل بموجب الاتفاقية |
| origin gap: cannot be checked, because the rule is not in Mansha's sources | لا يمكن فحصه، لأن القاعدة غير موجودة في مصادر منشأ |
| The checks that failed are listed under the rule of origin below. | الفحوص التي لم يجتزها المنتج مذكورة تحت قاعدة المنشأ أدناه. |
| Estimated saving: {x}. | التوفير التقديري: {x}. |
| Tariff line {line}: {description} (Mansha's confidence: {c}). Confirm the code with Indian customs or a customs broker before shipping. | البند الجمركي {line}: {description} (درجة ثقة منشأ: {c}). أكّد الرمز مع الجمارك الهندية أو مع مخلّص جمركي قبل الشحن. |
| Agreement: {agreement}. | الاتفاقية: {agreement}. |
| Rule of origin: {rule}. Result: the product {origin text}. {basis} | قاعدة المنشأ: {rule}. النتيجة: المنتج {origin text}. {basis} |

**Open point (not wording):** `{description}`, `{agreement}` and `{basis}` come from the KB and the tools in English. In an Arabic fallback they would stay English, unless the fallback leaves them out. That is decided when this part goes into the code.

## Part 3: already live, never reviewed by a native reader
These have been in Arabic reports since earlier steps. A careful read is worth it before the demo.
- **Checklist step texts (S3):** `step.ar` of the 7 step records in `data/india/passages.json`, and the fee step in `mansha/researcher.py` (around line 947).
- **Headings, result labels, disclaimer, cautions, checklist pointer:** `HEADINGS`, `RESULT_LABEL`, `DISCLAIMER`, `CONDITION_TEXT`, `FREE_ZONE_STEP_TEXT` and `CHECKLIST_POINTER` in `mansha/document_builder.py`.
  - **Point to check:** the title reads "فحص المنشأ من منشأ" ("origin check by Mansha", where منشأ is both the word "origin" and the product's name).
- **Stop messages:** the Arabic stop and question messages in `mansha/orchestrator.py`.

## Part 4: the LLM's term choices (Gemini, readings 015311 and 022326)
The Builder writes these itself, so a reviewed choice would go into the prompt or FACTS. Claude's reading is marked; the native reader decides.
- **The brand:** «منشأ», never «منشأة». Fixed in `90e2431` (FACTS give the Arabic name), with 0 slips in 022326. The grader counts it.
- **MFN has two names in one report:** the prose writes «الدولة الأكثر رعاية», the code's table header «الدولة الأولى بالرعاية» (all 4 runs). One should be chosen.
- **FOB:** «تسليم على متن السفينة» (015311 r2, 022326 r2) looks right. These look off: «تسليم السفينة» (015311 r1) and «السعر شامل التكاليف على ظهر السفينة» (022326 r1, which sounds like cost-included).
- **Non-originating:** «غير وطني المنشأ» and «غير حائز على المنشأ» (both read well); «غير منشأة» (015311 r1) is wrong.
- **Heading 7610:** «أبواب ونوافذ وأطرها وأعتابها» is right; «أجهزة الأبواب والنوافذ» (015311 r2) is wrong.
- **Currency:** 022326 r2 wrote «درهم إماراتي» where FACTS say "AED" (the prompt says to copy currencies exactly). Should an Arabic report keep "AED" or write «درهم»? The code's fee step already writes «درهم».
- **Smaller:** «الفرع الفرعي» (redundant, 015311 r2 and 022326 r2); «العمليات الأدنى» vs «العمليات الدنيا» (minimal operations); «الرمز المنسق» vs «رمز النظام المنسق» (HS code).
