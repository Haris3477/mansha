"""Offline tests for the rule lookup tool. Run: python -m scripts.test_rule_lookup"""

from mansha.tools.rule_lookup import find_rule, rule_lookup

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def va_min(rule):
    return [t.get("min_pct") for alt in rule["alternatives"] for t in alt if t["test"] == "VA"]


# --- lookup order, on fake rules (real data has chapter rows only) ---
ORDER = ["subheading", "heading", "heading_range", "ex_chapter", "chapter"]
FAKE = [
    {"id": "CH76", "scope": {"type": "chapter", "chapter": "76"}},
    {"id": "EX76", "scope": {"type": "ex_chapter", "chapter": "76"}},
    {"id": "H7610", "scope": {"type": "heading", "heading": "7610"}},
    {"id": "SH761010", "scope": {"type": "subheading", "subheading": "761010"}},
    {"id": "R7206", "scope": {"type": "heading_range", "from": "7206", "to": "7229"}},
    {"id": "BAD", "scope": {"type": "heading", "heading": "76"}},  # malformed: never matches
]
lvl, hits = find_rule(["76101000"], FAKE, ORDER)
check("subheading beats heading and chapter", lvl == "subheading" and [r["id"] for r in hits] == ["SH761010"])
lvl, hits = find_rule(["76109000"], FAKE, ORDER)
check("heading beats chapter", lvl == "heading" and [r["id"] for r in hits] == ["H7610"])
lvl, hits = find_rule(["76151030"], FAKE, ORDER)
check("ex_chapter beats chapter", lvl == "ex_chapter")
lvl, hits = find_rule(["72101100"], FAKE, ORDER)
check("heading range matches", lvl == "heading_range" and hits[0]["id"] == "R7206")
lvl, hits = find_rule(["72301000"], FAKE, ORDER)
check("outside range -> no match", lvl is None and hits == [])
lvl, hits = find_rule(["99999999", "76101000"], FAKE, ORDER)
check("HS-2017 alternative code is tried", lvl == "subheading")

# --- real knowledge base ---
r = rule_lookup("76101000")
check("windows: CTSH + VA 45%", r.status == "RULE_FOUND" and r.level == "chapter"
      and r.rules[0]["rule_text"] == "CTSH + VA 45%" and va_min(r.rules[0]) == [45], r.to_dict())
check("'+' interpretation attached", any("'+'" in i for i in r.interpretations), r.interpretations)
g = {x["id"]: x["applies_to_this_line"] for x in r.general_rules}
check("general rules flagged (FOB, EXW apply; HS71 not)",
      g.get("PSR-GEN-FOB") and g.get("PSR-GEN-EXW") and g.get("PSR-GEN-HS71") is False, g)
check("sources resolved to URLs", "R39-G" in r.sources and r.sources["R39-G"].startswith("https://"), r.sources)

r = rule_lookup("85044030")
check("chargers: CTH + VA 40%", r.status == "RULE_FOUND" and r.rules[0]["rule_text"] == "CTH + VA 40%",
      r.rules[:1])

r = rule_lookup("39239090")
check("excluded line still returns its rule (exclusion checked elsewhere)", r.status == "RULE_FOUND")

r = rule_lookup("71131910")
check("chapter 71 not loaded -> RULE_NOT_LOADED gap",
      r.status == "RULE_NOT_LOADED" and r.rules == [] and r.general_rules == []
      and any("REGULATORY_GAP_DETECTED" in n for n in r.notes), r.notes)

try:
    rule_lookup("7610")
    check("bad input raises ValueError", False)
except ValueError:
    check("bad input raises ValueError", True)

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")