# Brief: KB batch (72, 96, 101 + KB note wording), designed on paper 27 Oct 2026

Follows `docs/cloud/handoff_2026-10-26_fix_round_1.md` (fix round 1 closed). Status: **built and closed (27 Oct)**; Haris's choices, results and later changes (96 → note removed, 2A) in `docs/cloud/handoff_2026-10-27_kb_batch.md`. Each item: cause, options, Claude's recommendation, what should change and how we'll know.

Saved runs: extract `runs-snapshot` first (CLAUDE.md). Latest sittings: `runs/eval_set/20261027-155659`, `-163642`, `-172227` (Dots3).

## 1. Slip 72: actor of `P-MOET-COO-INDIA` (`data/india/passages.json`)
**Cause.** `prompts/researcher.md` says "name who acts only as the cited record's `actor:` line does". This record's actor is "the Ministry of Foreign Trade" (decision C, 15 Oct), but the record is MoET's "Certificate of Origin for India" page. Actor-first steps therefore produce 72: "the Ministry of Foreign Trade provides the Certificate of Origin for India e-service…" (041503 N5, Gemini); "The Ministry of Foreign Trade issues the certificate: log in…" (041503 C1, Dots3). 72 counted in 4 of 4 runs (041503), 2 of 4 (155659), 2 of 4 (163642), 3 of 4 (172227).
**Catch.** `mansha/tools/coo_fee.py` (line ~68) copies the fee's `actor` from this same record; `scripts/test_researcher.py` (~198) asserts that.

| Option | Change | Pro | Con |
|---|---|---|---|
| **A (recommended)** | actor → "the exporter"; the fee tool takes its actor from `P-UAE-ISSUER` (MoFT; that record says certificate fees are set in MoFT's fee resolution, CR 208/2025) | True to the record (every step in it is the applicant's); decision C unchanged; precedent `P-AGR-3.12-DIRECT` ("Authority: The exporter") | small code change in the fee tool; one test assertion changes |
| B | actor → "the Ministry of Economy and Tourism" | matches the page's publisher | contradicts decision C and the fee step (MoFT): reopens Haris's 15 Oct decision |
| C | prompt: steps start with the exporter's action, never the actor | also fixes 94 and Gemini's lower-case actor-first steps (G14) | prompt change on every step; belongs to the step shield |

Should change: 72 → ~0 in claim reports; the fee step still says MoFT. Know by: the 72 anchor count and reading the fee step. Risk: the record summary still names MoFT once ("lists the same fee bands"); the anchor's second branch catches "via the Ministry of Foreign Trade".

## 2. Slip 96: the box-9 note of `P-AGR-COO-RULES`
**Cause.** Note: "The agreement says box 8, but India's origin rules and certificate form say box 9; India's form governs entry into India." Models turn "governs" into an instruction ("you must use box 9", "require box 9 to be completed", "you must follow India's form"); 8+ saved reports, mostly in Notes. The note matters only for a certificate issued retrospectively (no current case).
- **A (recommended, KB only):** scope first: "Only for a certificate issued retrospectively: the agreement says box 8 for the 'ISSUED RETROSPECTIVELY' mark, but India's origin rules and certificate form say box 9; India's form governs entry into India." The Researcher's "skip notes that do not apply" rule should then drop it in normal cases.
- B: A plus code-verbatim printing (`FIXED_NOTE_IDS` in `mansha/evidence.py`, as for `P-UAE-ISSUER`). In reserve.
Should change: 96 stays 0 and the box-9 note mostly disappears from Notes. Note: the 96 anchor missed "you must follow India's form" (163642 N5); widen it with the fix (grader test).

## 3. Problem 101: `P-IN-IMPORTER` rewrite (e-certificate sentence)
**Cause.** The record states the e-certificate fact twice with stale hedging (summary "reportedly … (unconfirmed: seen only in secondary sources)"; note "read only through secondary reports (LiveLaw, taxmann), not the official text"). CBIC Instruction 28/2022 is PRIMARY since 17 Oct (fact base A6). QA churns the hedges; 101 = a wrong QA correction on them → qualifier check fails → CHECKS_FAILED.
**Source used in the cloud:** `docs/archive/browser_checks_2026-10-17.md` item 6 (the read A6 was built from): F. No. CBIC-15021/172/2022-ICD-CBEC, 27 Oct 2022; an e-CoO from the "Issuing Authority of UAE" is valid in the prescribed format with electronically printed seal and signature, meeting 39/2022-Customs (N.T.); mandatorily uploaded on e-Sanchit by the importer/customs broker, with reference number, date and origin criteria entered in the bill of entry; a printed copy presented for defacement at out-of-charge; a CoO reference number cannot be reused in another bill of entry; names no ministry.
- **B (recommended): minimal.** Replace the hedged summary sentence with "Electronic certificates from the UAE issuing authority are accepted and uploaded to e-Sanchit by the importer or customs broker."; drop the "secondary reports" note; `sources.json` `CBIC-INSTR-28` → PRIMARY, official title and URL; `provision` → "CBIC Instruction 28/2022-Customs (27 Oct 2022)". One variable: the hedges go, so 101 has nothing to churn.
- A: fuller: B plus the format/seal, bill-of-entry fields and no-reuse facts. More useful, but a longer step to merge or garble; better in the KB-URL step.
**Needed from Haris:** the A6 row, at least the exact official URL. Plain `taxinformation.cbic.gov.in/content/pdf/…` links show base64 JSON; exporter links need `view-pdf/1000447/ENG/<type>`, and `<type>` is unknown. Don't guess it.
**Cost:** ~8 test fixtures use this note as the live example of a qualified note (`scripts/test_researcher.py`, `test_kb_shield.py`, `test_document_builder.py`, `eval_qa.py`, `eval_prose_qa.py`); they move to another qualified note (`P-UAE-ISSUER`) or a synthetic record. The mechanisms (check 10, restore, KB shield) stay.

## 4. New (172227): raw "Inference:" labels and "SWS" in verbatim KB notes
Notes printed word for word (7.6e/7.6f, restore) reach the exporter as "Inference: SWS is charged on the reduced BCD (no CEPA-specific text found)." (N2, N5, C1). Not yet designed. To decide with Haris: reword the KB notes in plain words while keeping a qualifier word the checks know (e.g. "Likely: …", "Social Welfare Surcharge (SWS)"), versus a Builder rendering rule. Any rewording must keep the qualifier (check 10, KB shield).

## Bundle and measurement
Claude's recommendation: build 72, 96, 101 together (different records and anchors, separable), item 4 after its design. Offline: check_data, all 19 suites, replays of saved reports (72/96 anchors). Live: N5, N10, C1, N2 at k = 1 on Dots3. Expect 72 ≈ 0, 96 = 0, no e-certificate hedge churn, the fee step still MoFT.
