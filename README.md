Mansha (منشأ) — CEPA origin check for UAE exporters

Mansha tells a UAE exporter whether a product qualifies for reduced or zero customs duty under a UAE Comprehensive Economic Partnership Agreement (CEPA), proves the answer with the agreement's own rules of origin, and lists the steps to claim it, in Arabic or English.

The first corridor is UAE → India. The design is meant to be extended to other CEPA partners (see Adding a corridor).

Status: pre-release, built for the Create AI Agents Championship (Dubai Chamber of Digital Economy) and a December 2026 hackathon. Expect rough edges.

Not legal or customs advice. Mansha's output is a pre-check. Always verify with the competent authority (UAE Ministry of Economy and Tourism / Ministry of Foreign Trade, and the partner country's customs) before shipping or claiming a preference.

Why

Small and medium UAE manufacturers and processors often cannot tell whether their goods qualify for a CEPA preference, and checking rules of origin by hand against tariff lines, product-specific rules and bills of materials is slow. Traders and re-exporters whose goods do not qualify should get a clear "no" and the reason, not a guess.

How it works

Four agents, each a separate LLM call orchestrated in plain Python (mansha/orchestrator.py), with deterministic tools between them:

user text
   |
   v
Intake Agent ---------> structured fields (product, HS code, destination, role, processing, value, language)
   |
   v
Deterministic tools (plain Python, no LLM): tariff lookup, rule lookup,
origin calculator (applies the agreement's rule to a bill of materials),
duty estimate, certificate-of-origin fee
   |
   v
Researcher Agent ------> picks the tariff line, normal vs CEPA rate, rule of origin,
   |                     qualification result, steps to claim; every item cites a source
   v
QA Evaluator Agent ----> a different model scores Factuality / Completeness / Formatting safety;
   |                     code sets APPROVED or REJECTED; one revision loop at most
   v
Document Builder Agent -> Markdown origin-check report: checklist, sources, disclaimer

Design rules:

LLMs never do arithmetic. Every number comes from the deterministic tools.
Grounded in official texts. The knowledge base (data/india/) is built from official CEPA texts and government sources listed in data/india/sources.json. Anything not supported by a retrieved source is flagged REGULATORY_GAP_DETECTED instead of guessed.
Confidential business data stays in code. Input costs and supplier details are read only by code; prompts receive counts and percentages only.
Visible QA loop. The pipeline prints every phase's log, so you can see the evaluator reject and the revision happen.
Quick start

Requires Python 3.13.

bash
git clone https://github.com/Haris3477/mansha.git
cd mansha
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then edit .env
Offline tests (no LLM, no network)
bash
python -m scripts.check_data
python -m scripts.test_tariff_lookup
python -m scripts.test_rule_lookup
python -m scripts.test_origin_calculator
python -m scripts.test_duty_estimate
python -m scripts.test_coo_fee
Live pipeline

Mansha calls an OpenAI-compatible endpoint through the openai SDK. Set the endpoint and key in .env:

FREELLMAPI_BASE_URL=http://localhost:3001/v1
FREELLMAPI_KEY=your-key-here

The agents request model chains by name (auto:qa for Intake, auto:long for the Researcher and Document Builder, auto:judge for the QA Evaluator and prose check). Our development setup uses a self-hosted router that maps these names to free and paid models. To use another provider, change the model names in mansha/llm_client.py. The QA judge is deliberately a different model from the writer.

Then run the sample cases:

bash
python -m scripts.run_pipeline                      # all sample cases
python -m scripts.run_pipeline windows chargers     # selected cases

Each run writes the phase log and the Markdown report under runs/ (git-ignored).

Sample inputs (bill-of-materials CSV plus a declaration JSON) are in samples/; the samples/eval/ folders are synthetic companies and costs.

Repository layout
mansha/       agents and pipeline (intake, researcher, qa, document_builder, orchestrator, kb, llm_client)
mansha/tools/ deterministic tools (tariff_lookup, rule_lookup, origin_calculator, duty_estimate, coo_fee)
prompts/      agent prompts (Markdown)
data/india/   UAE -> India knowledge base (sources, tariff lines, product-specific rules, passages)
samples/      synthetic example inputs and saved outputs
scripts/      runners, offline tests and evaluation scripts
docs/         runbook and design notes
Adding a corridor

A corridor is a set of data files plus an entry in the knowledge-base loader:

Create data/<corridor>/ with sources.json, tariff_lines.json, psr_rules.json and passages.json, following the structure in data/india/.
Use official sources only (ministry, customs and commerce authorities, the agreement text and annexes) and record each in sources.json.
Register the corridor in mansha/kb.py (CORRIDORS).
Run python -m scripts.check_data and add sample cases under samples/.

Never invent HS codes, rates, rules of origin, article numbers, fees or timelines. If something cannot be found in an official source, leave it as a gap.

Contributing

Issues and pull requests are welcome, especially new corridors, corrections to rules or rates (with an official source), Arabic wording review, and tests. Please use synthetic data only; do not commit real company data or API keys.

License

Licensed under the Apache License, Version 2.0. See NOTICE.
