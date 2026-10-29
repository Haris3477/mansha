"""Build a phone-friendly PDF for a native Arabic reader to check Mansha's Arabic.

Input: arabic_strings.json, extracted from the code and docs/cloud/arabic_review.md by script
(no Arabic is retyped here, except the few short Arabic placeholder labels in FILL).
Output: mansha_arabic_review.pdf and arabic_review_items.md (number -> where it lives in the code).
"""
import html
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

S = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
OUT = Path(sys.argv[2])
FONTS = Path(__file__).parent / "node_modules/@fontsource"

# Placeholders filled by the program -> what the reader sees (example value or a grey label)
FILL = {
    "{t}": "10%", "{e}": "10%", "{x}": "10000.00 AED", "{line}": "76101000", "{rule}": "CTSH + VA 45%",
    "{fee}": "50", "{value}": "100,000", "{min}": "10", "{max}": "200",
    "{description}": "[الوصف]", "{agreement}": "[اسم الاتفاقية]", "{basis}": "[سبب النتيجة]",
    "{origin text}": "[نتيجة الفحص]", "{c}": "[درجة الثقة]",
}
FILL_EN = {"{t}": "10%", "{e}": "10%", "{x}": "10000.00 AED", "{line}": "76101000", "{rule}": "CTSH + VA 45%",
           "{fee}": "50", "{value}": "100,000", "{min}": "10", "{max}": "200", "{description}": "[description]",
           "{agreement}": "[agreement name]", "{basis}": "[reason for the result]",
           "{origin text}": "[check result]", "{c}": "[confidence]"}
PH = re.compile("|".join(re.escape(k) for k in sorted(FILL, key=len, reverse=True)))


def fill(text: str, table: dict) -> str:
    out, last = [], 0
    for m in PH.finditer(text):
        out.append(html.escape(text[last:m.start()]))
        out.append(f'<bdi class="ph">{html.escape(table[m.group(0)])}</bdi>')
        last = m.end()
    out.append(html.escape(text[last:]))
    return "".join(out).replace("\n", "<br>")


items, mapping, n = [], [], 0


def add(section, en, ar, where, note=None):
    global n
    n += 1
    items.append({"kind": "text", "section": section, "n": n, "en": en, "ar": ar, "note": note})
    mapping.append((n, section, where, en))


def choose(section, question, options, where, note=None):
    global n
    n += 1
    items.append({"kind": "choose", "section": section, "n": n, "en": question, "options": options, "note": note})
    mapping.append((n, section, where, question))


p4 = S["p4"]
C1 = "1. Choose one"
choose(C1, "“MFN”: the normal customs duty rate (without the trade agreement). One report used two names for it. Which one should we use everywhere?",
       [p4["MFN has two names in one report"][1], p4["MFN has two names in one report"][0]],
       "Part 4: MFN name (code table header uses a; the AI wrote b)")
choose(C1, "“FOB” (Free On Board): a price that includes delivery onto the ship. Which Arabic is right?",
       p4["FOB"], "Part 4: FOB", note="If none is right, write the correct one.")
cond_ar = S["conditions"][1][1]
assert "غير ذات منشأ" in cond_ar
choose(C1, "“Non-originating materials”: inputs that do NOT count as made in the UAE or India under the agreement’s rules. Which is right (more than one can be OK)?",
       p4["Non-originating"] + ["غير ذات منشأ"], "Part 4: non-originating (d is used in the code's caution text)",
       note="c) was written by the AI once; we think it is wrong.")
choose(C1, "“Minimal operations”: very simple work (packing, labelling, sorting…) that does not make a product ‘made in the UAE’. Which is right?",
       [p4["Smaller"][2], p4["Smaller"][1]], "Part 4: minimal operations")
msg_hs = "الرمز الجمركي"
assert msg_hs in S["msgs"][1][1]
choose(C1, "“HS code”: the international customs code of a product (e.g. 7610.10). Which should we use?",
       [p4["Smaller"][4], p4["Smaller"][3], msg_hs], "Part 4: HS code (c is used in the app's messages)")
choose(C1, "Currency in an Arabic report: for amounts like “10000.00 AED”, what reads best?",
       ["AED", p4["Currency"][1], p4["Currency"][0]], "Part 4: currency (the fee step in code already writes b)")
choose(C1, "“Subheading”: the 6-digit level of the HS code. The AI wrote this. Is it correct?",
       [p4["Smaller"][0]], "Part 4: subheading", note="Reply ✓, or write the usual Arabic term.")
choose(C1, "The product group for HS 7610: “Doors, windows and their frames and thresholds for doors”. Is this Arabic right?",
       [p4["Heading 7610"][0]], "Part 4: heading 7610", note=f"(The AI once wrote «{p4['Heading 7610'][1]}», which we think is wrong.)")
title_ar = dict(S["headings"])["Mansha origin check"]
choose(C1, "The app’s name is «منشأ» (it means “origin”). The report title is “Mansha origin check”. Does this title read well, or is it confusing because the same word appears twice?",
       [title_ar], "Part 3: HEADINGS title + brand", note="Reply ✓, or suggest a better title.")

C2 = "2. New texts (not in the app yet)"
for en, ar in S["saving"]:
    add(C2, f"Duty table, “saving” cell: {en}", ar, "Part 2: saving cell (saving_text)")
for en, ar in S["mfn"]:
    add(C2, f"Duty table, normal-rate cell: {en}", ar, "Part 2: MFN cell")
for title, en, ar in S["notes"]:
    add(C2, f"Note ({title}): {en}", ar, f"Part 2: verbatim note: {title}")
def prose_label(en: str) -> str:
    """'NOT_ELIGIBLE: the product …' -> 'Short report text (result: not eligible): the product …'."""
    m = re.match(r"^(origin )?([A-Z_]+|gap): (.+)$", en)
    if not m:
        return f"Short report text: {en}"
    kind = m.group(2).lower().replace("_", " ")
    what = "origin check" if m.group(1) else "result"
    return f"Short report text ({what}: {kind}): {m.group(3)}"


for en, ar in S["prose"]:
    add(C2, prose_label(en), ar, f"Part 2: code-only prose: {en[:60]}")

C3 = "3. Already in the app"
for en, ar in S["authority"].items():
    add(C3, f"Who acts in a step: {en}", ar, "Part 1: AUTHORITY_TEXT")
add(C3, "Notice: the explanation in this report could not be prepared in Arabic at sufficient quality, so it is shown in English.",
    S["fallback_notice"], "Part 1: FALLBACK_NOTICE")
for en, ar in S["headings"]:
    add(C3, f"Report heading / label: {en}", ar, "Part 3: HEADINGS")
for en, ar in S["result"]:
    add(C3, f"Result line: {en}", ar, "Part 3: RESULT_LABEL")
add(C3, S["disclaimer"][0], S["disclaimer"][1], "Part 3: DISCLAIMER")
for en, ar in S["conditions"]:
    add(C3, en, ar, "Part 3: CONDITION_TEXT")
add(C3, S["free_zone_step"][0], S["free_zone_step"][1], "Part 3: FREE_ZONE_STEP_TEXT")
add(C3, S["pointer"][0], S["pointer"][1], "Part 3: CHECKLIST_POINTER")
for pid, en, ar in S["steps"]:
    add(C3, f"Checklist step: {en}", ar, f"Part 3: step text {pid} (data/india/passages.json)")
for en, ar in S["fee"]:
    add(C3, f"Checklist step: {en}", ar, "Part 3: FEE_STEP (mansha/researcher.py)")
for en, ar in S["ask"]:
    add(C3, f"App message: {en}", ar, "Part 3: orchestrator ASK / ASK_INTRO / ASK_END")
for i, (en, ar) in enumerate(S["msgs"]):
    add(C3, f"App message: {en.strip()}", ar.strip(), "Part 3: orchestrator stop messages",
        note=("Known issue: the country list is filled in English (\u201cIndia\u201d); we will fix that in the app, "
              "so only check the rest.") if i == 0 else None)

counts = {}
for it in items:
    counts.setdefault(it["section"], []).append(it["n"])

font_ar = (FONTS / "noto-naskh-arabic/files").resolve()
font_la = (FONTS / "noto-sans/files").resolve()
css = f"""
@font-face {{ font-family: Naskh; font-weight: 400; src: url('file://{font_ar}/noto-naskh-arabic-arabic-400-normal.woff2'); }}
@font-face {{ font-family: Naskh; font-weight: 700; src: url('file://{font_ar}/noto-naskh-arabic-arabic-700-normal.woff2'); }}
@font-face {{ font-family: NSans; font-weight: 400; src: url('file://{font_la}/noto-sans-latin-400-normal.woff2'); }}
@font-face {{ font-family: NSans; font-weight: 700; src: url('file://{font_la}/noto-sans-latin-700-normal.woff2'); }}
@page {{ size: A5; margin: 12mm 11mm 13mm 11mm; }}
body {{ font-family: NSans, Naskh, sans-serif; font-size: 10.5pt; color: #1d1d1f; line-height: 1.45; margin: 0; }}
h1 {{ font-size: 17pt; margin: 0 0 2mm; }}
h2 {{ font-size: 13pt; margin: 6mm 0 1mm; padding-bottom: 1.5mm; border-bottom: 2px solid #0b6e4f; color: #0b6e4f; break-after: avoid; }}
.sub {{ color: #555; font-size: 9.5pt; margin: 0 0 3mm; }}
.box {{ background: #f2f7f5; border-radius: 3mm; padding: 3mm 4mm; margin: 3mm 0; }}
.box p {{ margin: 1.2mm 0; }}
.item {{ break-inside: avoid; border: 1px solid #ddd; border-radius: 3mm; padding: 2.5mm 3.5mm 3mm; margin: 2.6mm 0; }}
.num {{ display: inline-block; min-width: 7mm; padding: 0 1.6mm; border-radius: 2mm; background: #0b6e4f; color: white;
        font-weight: 700; text-align: center; margin-right: 2mm; font-size: 10pt; }}
.en {{ color: #444; font-size: 9.5pt; }}
.ar {{ direction: rtl; text-align: right; font-family: Naskh, serif; font-size: 14.5pt; line-height: 1.75; margin-top: 1.5mm;
       unicode-bidi: plaintext; }}
.opt {{ direction: rtl; text-align: right; font-family: Naskh, serif; font-size: 14.5pt; line-height: 1.7; margin: 1mm 0; }}
.letter {{ font-family: NSans; font-weight: 700; font-size: 10.5pt; display: inline-block; width: 6mm; height: 6mm; line-height: 6mm;
          text-align: center; border-radius: 50%; background: #e3efe9; color: #0b6e4f; margin-left: 2mm; }}
.note {{ color: #7a5a00; font-size: 9pt; margin-top: 1mm; }}
.ph {{ background: #e8e8ed; border-radius: 1.5mm; padding: 0 1.2mm; font-weight: 700; color: #333; }}
.tag {{ font-weight: 700; color: #0b6e4f; }}
"""
parts = [f"<style>{css}</style>",
         "<h1>Mansha: Arabic check</h1>",
         "<p class='sub'>For a native Arabic reader · about 20–30 minutes for everything, 10 for the most important part</p>",
         "<div class='box'>",
         ("<p><b>What is this?</b> Mansha (<span style='font-family:Naskh'>منشأ</span>, “origin”) is an AI app that tells UAE "
         "companies whether their product pays lower customs duty in India under the UAE–India trade agreement (CEPA), and "
         "writes a report in English or Arabic. Before I show it to judges, I need someone who reads Arabic to check the Arabic.</p>"),
         ("<p><b>What to check:</b> does it read correctly and naturally, and does it mean the same as the English line above it? "
         "No trade knowledge needed.</p>"),
         "<p><b>How to reply on WhatsApp:</b> the number, then:</p>",
         "<p>✓ if it is fine &nbsp;·&nbsp; your corrected Arabic if not &nbsp;·&nbsp; a letter for “choose” items.</p>",
         ("<p>Example: <b>3 b</b> &nbsp;·&nbsp; <b>12 ✓</b> &nbsp;·&nbsp; <b>15 → (your Arabic)</b>. "
         "You can also reply “all ✓ except …”.</p>"),
         ("<p><span class='ph'>Grey boxes</span> are filled in by the app (a number or a name), so skip them. English words "
         "inside the Arabic (CIF, IGST, e-Sanchit, website addresses) are on purpose.</p>"),
         (f"<p><b>Most important:</b> parts 1 and 2 (items {counts[C1][0]}–{counts[C2][-1]}). Part 3 is already in the app; "
         "check it if you have time.</p>"),
         "</div>"]
section = None
for it in items:
    if it["section"] != section:
        section = it["section"]
        sub = {C1: "The app or the AI used different words for the same thing. Pick the best (or write your own).",
               C2: "New Arabic sentences, waiting for your check before they go into the app.",
               C3: "Arabic already shown in reports and messages. Never checked by a native reader."}[section]
        head = f"<h2>{html.escape(section)}</h2><p class='sub'>{sub}</p>"
    else:
        head = ""
    en_html = fill(it["en"], FILL_EN)
    block = [f"<div style='break-inside: avoid'>{head}<div class='item'><span class='num'>{it['n']}</span><span class='en'>{en_html}</span>"]
    if it["kind"] == "text":
        block.append(f"<div class='ar'>{fill(it['ar'], FILL)}</div>")
    else:
        for i, o in enumerate(it["options"]):
            letter = "abcde"[i] if len(it["options"]) > 1 else "✓"
            block.append(f"<div class='opt'><span class='letter'>{letter}</span>{html.escape(o)}</div>")
    if it.get("note"):
        block.append(f"<div class='note'>{html.escape(it['note'])}</div>")
    block.append("</div></div>")
    parts.append("".join(block))
parts.append("<div class='box' style='margin-top:6mm'><p><b>Thank you!</b> Any other comment about the Arabic is very welcome.</p></div>")

doc = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>" + "".join(parts) + "</body></html>"
(OUT / "review.html").write_text(doc, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(f"file://{(OUT / 'review.html').resolve()}")
    pg.wait_for_timeout(500)
    pg.pdf(path=str(OUT / "mansha_arabic_review.pdf"), format="A5", print_background=True,
           display_header_footer=True, header_template="<span></span>",
           footer_template="<div style='font-size:7pt;width:100%;text-align:center;color:#888'>"
                           "Mansha Arabic check · <span class='pageNumber'></span>/<span class='totalPages'></span></div>",
           margin={"top": "12mm", "bottom": "13mm", "left": "11mm", "right": "11mm"})
    b.close()

md = ["# Arabic review: item numbers in the PDF", "",
      ("The PDF `mansha_arabic_review.pdf` numbers every item. When the reader replies (e.g. \"12 → …\"), this table says "
      "where the text lives. Generated from `runs/inspect/arabic_strings.json` (extracted from the code and "
      "`docs/cloud/arabic_review.md`), 29 Oct 2026."), "", "| # | Section | Where | English |", "|---|---|---|---|"]
for num, sec, where, en in mapping:
    md.append(f"| {num} | {sec.split('. ')[0]} | {where} | {en[:90].replace('|', '/')}{'…' if len(en) > 90 else ''} |")
(OUT / "arabic_review_items.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(n, "items;", {k: (v[0], v[-1]) for k, v in counts.items()})
