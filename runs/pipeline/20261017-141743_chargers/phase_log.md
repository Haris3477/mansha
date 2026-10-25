# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 112.02 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 3.17 | groq/openai/gpt-oss-120b | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 20225 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 46.01 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | SKIPPED | 0.0 | - | QA Evaluator not built yet (Step 7): output NOT reviewed by QA |
| 6 | Document Builder | OK | 62.83 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the checks; notes: 4 in (2 mandatory, verbatim) -> 4 in the report |
| 7 | Report check | OK | 0.01 | - | 0 problem(s), 4 warning(s); report shown anyway (flag only) |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (3.17 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 20225 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (46.01 s)

### 5. QA (round 1): SKIPPED

QA Evaluator not built yet (Step 7): output NOT reviewed by QA

### 6. Document Builder: OK

LLM prose passed the checks | notes: 4 in (2 mandatory, verbatim) -> 4 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (62.83 s)

### 7. Report check: OK

0 problem(s), 4 warning(s) | report shown anyway (flag only)

Warnings:
- NOT_ELIGIBLE report mentions claiming ('Factory Registration'): …a free zone is likely not eligible for Factory Registration, which is needed before applying for th…
- NOT_ELIGIBLE report mentions claiming ('certificate of origin'): …which is needed before applying for the certificate of origin for India. Confirm with the Ministry of…
- NOT_ELIGIBLE report mentions claiming ('issuer'): …es the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifica…
- NOT_ELIGIBLE report mentions claiming ('e-Sanchit'): …are reportedly accepted and uploaded to e-Sanchit, but this is unconfirmed (seen only in…
