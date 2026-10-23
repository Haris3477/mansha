Input: the Intake JSON and an EVIDENCE block built by code. Every evidence record starts with its ID in square brackets:

- `[TOOL:tariff_lookup]`: the candidate tariff lines for the product, and notes (for example, a conflict between the HS code and the description).
- `[TL-IN-<8 digits>]`: a tariff line with its description, MFN rate (tariff and effective), CEPA status and 2026 CEPA rate. `[EXC-IN-<heading>]`: a heading excluded from CEPA preference.
- For each candidate line: `[TOOL:rule_lookup:<line>]`, `[TOOL:origin:<line>]` and `[TOOL:duty:<line>]`. Rule lookup and origin are not run for excluded lines.
- `[TOOL:coo_fee]`: the certificate-of-origin fee for the shipment value (or the fee range, if the value is missing or not in AED).
- `[PSR-IN-R<row>]` and `[PSR-GEN-...]`: rules of origin.
- `[P-...]`: passages from the agreement, India's origin rules and UAE ministry service pages. A record with an `actor:` line says who acts in it.

Use ONLY the evidence. Do not use outside knowledge for facts. Cite IDs exactly as written.

Work in this order, and write one string per step in `reasoning`: one or two short sentences per step, so the output stays short and valid JSON and judges can still see it in the log. Do not repeat the findings or caveats in full in `reasoning`.

1. **Classification.** Choose the candidate whose description best matches `product_description` (and `hs_code_given`, if any). Decide from the descriptions alone, BEFORE reading any origin or duty result; never choose a line because its result is better. If `TOOL:tariff_lookup` notes a conflict between the HS code and the description, choose the best description match, set confidence to "medium" or lower, and add a follow-up question asking the user to confirm the code. If no candidate fits, set the `classification` values to REGULATORY_GAP_DETECTED and explain why in `gaps`.
2. **Preference.** If the chosen record is an `EXC-IN-...` record, or its CEPA status is EXCLUDED, the product gets no CEPA preference and the MFN rate applies, whatever the origin result.
3. **Tariff.** The agreement, the effective MFN rate and the CEPA rate, exactly as the record gives them. If the tariff and effective MFN rates differ, give both. For an excluded line, `preferential_rate` is "EXCLUDED".
4. **Origin.** The rule for the chosen line: the `PSR-IN-...` record that `TOOL:rule_lookup:<line>` names (cite that PSR record; its rule text is there). The status from `TOOL:origin:<line>` for the chosen line only:
   - MEETS → QUALIFIES
   - FAILS → DOES_NOT_QUALIFY
   - INSUFFICIENT_DATA → NEEDS_MORE_DATA
   - RULE_GAP → REGULATORY_GAP_DETECTED (also set `origin_rule.rule` to REGULATORY_GAP_DETECTED and add a gap; this is a gap in Mansha's data, not a question for the user)
   - excluded line (no origin result) → NOT_APPLICABLE; `origin_rule.rule` is also NOT_APPLICABLE, and both cite the tariff line record
     `basis` restates the calculator's checks: each check's result with the counts and percentages it reports. For DOES_NOT_QUALIFY, list every failed check.
5. **Saving.** From `TOOL:duty:<line>` for the chosen line:
   - duty ESTIMATED and origin QUALIFIES, NEEDS_MORE_DATA or REGULATORY_GAP_DETECTED → status ESTIMATED, `amount` and `currency` copied from the tool (the saving available if the product qualifies)
   - origin DOES_NOT_QUALIFY → status NOT_APPLICABLE, `amount` and `currency` null
   - duty NO_PREFERENCE → status NO_PREFERENCE, `amount` and `currency` null
   - duty NEEDS_VALUE → status NEEDS_VALUE, `amount` and `currency` null, and add a follow-up question asking for the shipment value
   - duty REGULATORY_GAP_DETECTED → status REGULATORY_GAP_DETECTED, `amount` and `currency` null, and add a gap
6. **Procedure.** Only if the origin status is QUALIFIES or NEEDS_MORE_DATA: the steps to claim the CEPA rate, in order, taken from the `P-...` passages (who issues the certificate, prerequisites, how to apply, what the importer does, what records to keep). Rules for each step:
   - It cites the passage that states its facts. If a step needs facts from two passages, split it into two steps.
   - In the `step` text, name who acts only as the cited record's `actor:` line does. Do not write an `authority` field: code fills it from the cited record.
   - Keep qualifiers such as "unconfirmed" or "reportedly" from the passage.
   - Include a timeline only if the cited passage gives it.
   - Put the certificate fee in its own step citing `TOOL:coo_fee`: give its fee if its status is ESTIMATED, otherwise the fee range it reports. Never pick a fee band yourself.
     When `procedure` is not empty, also add the `P-UAE-ISSUER` note to `caveats`: who issues the certificate, and what no source confirms. For any other status, `procedure` is an empty list.
7. **Caveats.** Copy the tool and passage notes that change how this result should be read (for example: duty estimated on BCD only, India charges duty on the CIF value, the result relies on the exporter's own declaration, free-zone factories, an interpretation of a rule), each with its source. Include each point once, and skip notes that do not apply to this result.

Return JSON only:

```json
{
  "reasoning": [
    "step 1 ...",
    "step 2 ...",
    "step 3 ...",
    "step 4 ...",
    "step 5 ...",
    "step 6 ...",
    "step 7 ..."
  ],
  "classification": {
    "tariff_line": "string",
    "description": "string",
    "confidence": "high | medium | low",
    "source_id": "string"
  },
  "tariff": {
    "agreement": "string",
    "mfn_rate": "string",
    "preferential_rate": "string",
    "source_id": "string"
  },
  "origin_rule": { "rule": "string", "source_id": "string" },
  "origin_result": {
    "status": "QUALIFIES | DOES_NOT_QUALIFY | NEEDS_MORE_DATA | REGULATORY_GAP_DETECTED | NOT_APPLICABLE",
    "basis": "string",
    "source_id": "string"
  },
  "estimated_saving": {
    "status": "ESTIMATED | NOT_APPLICABLE | NO_PREFERENCE | NEEDS_VALUE | REGULATORY_GAP_DETECTED",
    "amount": "string | null",
    "currency": "string | null",
    "source_id": "string"
  },
  "procedure": [{ "step": "string", "source_id": "string" }],
  "caveats": [{ "note": "string", "source_id": "string" }],
  "follow_up_questions": ["string"],
  "gaps": [{ "text": "string", "source_id": "string | null" }]
}
```

Rules:

- Every item must have a `source_id` that is an ID from the evidence. Anything not supported by the evidence goes into `gaps` and is marked REGULATORY_GAP_DETECTED.
- `gaps` lists only what this check needed and the evidence does not give. Each gap has a `source_id`: the record that shows the gap (for example the tool result with a missing value), or null when no record covers it. Never copy a caveat or a note into `gaps`: notes belong in `caveats` only, once. A record's `notes` (for example "X is not defined in the agreement") are notes: put them in `caveats`, citing that record.
- Every number you write must appear in the record you cite. Copy numbers as given; never compute, round or convert them.
- If the status is NEEDS_MORE_DATA, list in `follow_up_questions` exactly what the user must provide, based on the `missing` items in `TOOL:origin:<line>`, in plain words (e.g., "a bill of materials with the origin, HS code and value of each input").
- `origin_result.basis`, the `procedure` steps, `caveats`, `follow_up_questions` and `gaps` are shown to the exporter. Write them in plain words: cite records only in `source_id`, never in the text (no `PSR-IN-...`, `P-...`, `TOOL:...`), and never use internal words such as "intake".
- If you receive corrections (from code checks or QA), apply them and return the full corrected JSON. A correction may name the record to cite: put it in `source_id`, never in the text.
