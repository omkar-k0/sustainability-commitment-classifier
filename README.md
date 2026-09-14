# sustainability-commitment-classifier

Reads corporate sustainability report PDFs and splits environmental commitments into
**quantified** (has a figure and a target year) vs. **vague**. Built as a booth demo for
STATION Berlin, 16-17 Sept: five DAX companies, ranked by what share of their environmental
commitments are checkable, with real sentences from their own reports.

**What this tool does NOT claim:** it does not detect greenwashing, verify whether any
number is true, or assess a company's actual sustainability performance. It only measures
whether a commitment sentence is *checkable* -- does it name a figure and a target year --
never whether the company is telling the truth.

## Known weaknesses (read before trusting the numbers)

- **The classifier is a rule, not a model.** It is pure regex: a sentence with a number and
  a year is marked "quantified" even if the number is irrelevant or the sentence is
  otherwise meaningless. It has no understanding of context.
- **It never verifies any number.** A "quantified" commitment could still be false,
  outdated, or misleading -- the tool only checks that a figure and a year are present in
  the sentence.
- **Five companies is not a study.** This is a demo sample, not a statistically meaningful
  comparison of corporate behavior.
- **English-language reports only.** Reports are matched against English forward-looking
  and environmental-topic keyword lists; a German-only report would not be classified
  correctly.
- **PDF text extraction is imperfect.** Multi-column layouts, tables, and sidebars can get
  interleaved by the PDF text extractor, producing sentences that are technically valid
  English but read a bit jumbled. The report favors more legible sentences for display, but
  some noise gets through.

## How to run

```bash
pip install pdfplumber
python3 scripts/extract.py   # PDF -> data/<company>.txt (cached, runs once per PDF)
python3 scripts/pipeline.py  # segment -> filter -> classify -> aggregate, prints per-company counts, writes cache/results.json
python3 scripts/render.py    # cache/results.json -> report.html
```

Or all at once:

```bash
python3 scripts/run_all.py
```

`report.html` is the final deliverable: a single self-contained file with no CDN links, no
scripts fetched at runtime, no server. Open it directly in a browser, offline.

Extracted plain text is cached in `data/` (committed) and the intermediate aggregate is
cached in `cache/results.json`, so `pipeline.py` and `render.py` run without needing the
source PDFs at all. Source PDFs go in `raw/` (gitignored -- large binaries, not needed once
`data/*.txt` exists); `scripts/extract.py` only touches `raw/` when the matching
`data/<company>.txt` is missing.

## Method

1. **Segment**: naive split on sentence-ending punctuation; sentences under 40 or over 400
   characters are discarded.
2. **Filter to commitments**: keep sentences with a forward-looking marker (will, aim,
   target, plan, commit, intend, "by 20xx", reduce, achieve, goal) AND an environmental
   topic keyword (emissions, climate, energy, water, waste, circular, etc.) -- both are
   plain regex, no ML.
3. **Classify**: a sentence needs both a number (percentage, unit figure like tCO2e/MWh/
   tonnes, or a plain integer > 1) and a target year (2025-2050) to count as Quantified;
   otherwise it's Vague.
4. **Aggregate**: per company, quantified count / vague count / quantified percentage.

Companies covered: Siemens, BASF, SAP, Henkel, Bosch (most recent English-language
sustainability/integrated report available from each company's own investor-relations
site as of September 2026).
