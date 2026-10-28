# Brief: the Arabic brand name in the Builder's prose ("منشأة" instead of "منشأ")

Background: `docs/cloud/handoff_2026-10-28_arabic_n15.md` (B section) and `docs/cloud/readings/20261029-015311_reading.md` (new problem 1). Base: branch `claude/arabic-router-chain-tvwgx1` at the commit of this brief. B is closed as holding (Haris, 29 Oct).

## The problem
In both Gemini runs, the Arabic prose writes the brand "Mansha" as "منشأة" (establishment, facility) instead of "منشأ" (origin), twice per run:
- "لا يمكن لمنصة منشأة";
- "بدرجة ثقة عالية من منشأة";
- "مستوى ثقة منشأة".

The title, printed by code, is right ("فحص المنشأ من منشأ").

**Where it likely comes from:** the Builder only ever sees the English name.
- `prompts/document_builder.md` says "Mansha" (lines 3, 35, 37, 38, 51).
- FACTS says "(Mansha's confidence: …)" (`mansha/document_builder.py` around lines 522 and 677).
- "Mansha" is in `LATIN_TERMS` (line 189).

**Why code can't simply flag it:** "منشأة" is also an ordinary Arabic word, so a blunt check would raise false alarms.

## Step 1 (cloud): design on paper, options + recommendation, then stop for Haris's yes
Options to weigh, among others:
1. **The name in FACTS:** in an Arabic report, FACTS carries the Arabic brand name (e.g. "(ثقة منشأ: …)").
2. **A prompt line:** "In Arabic, the product's name is «منشأ», never «منشأة»." This is a prompt change, so the Project's agent_prompts must be updated.
3. **A narrow code check:** flag only the brand phrases ("منصة منشأة", "من منشأة" next to confidence or result words), and correct them in the one retry.
4. **A combination of these.**

For each option, say:
- what it should change, and how the sitting will show it;
- the false-alarm risk;
- whether English reports are untouched.

## Step 2 (after the yes)
1. Make the change, with tests: the brand phrase is caught or prevented, the ordinary "منشأة" is not flagged, and English is unchanged.
2. Run all 20 suites, then commit and push.
3. **🖥️ sitting: N15 ×2.** The repeat also adds to B's sample.
4. **Full reading:**
   - "منشأ" used correctly, with 0 "منشأة" brand slips;
   - the B targets again: a Gemini call at ordinal 0 in `auto:arabic`, a clean round 1, no chain fallback;
   - the wrong-term list from the 015311 reading.
