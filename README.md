# sustainability-commitment-classifier

Reads corporate sustainability report PDFs and splits environmental commitments into
**quantified** (has a figure and a target year) vs. **vague**. Built as a booth demo for
STATION Berlin, 16-17 Sept: five large German companies (four DAX members plus Bosch), ranked by what share of their environmental
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

## Results

Environmental commitment sentences per company, from the cached report text in `data/`.

| Company | Commitments | Quantified | Share quantified |
|---|---:|---:|---:|
| Siemens | 298 | 34 | 11.4% |
| BASF | 487 | 30 | 6.2% |
| SAP | 166 | 18 | 10.8% |
| Henkel | 484 | 22 | 4.5% |
| Bosch | 127 | 16 | 12.6% |
| **All five** | **1562** | **120** | **7.7%** |

Reproduce: `python3 scripts/pipeline.py` (no PDFs needed). `pytest` checks these totals.

### Correction, 21 Nov 2026

Until this date the "has a number" check also matched the target year itself, so a sentence
like "we will reduce emissions significantly by 2030" counted as quantified. In practice
*Quantified* meant only *names a year*. Years and scope labels ("Scope 1 and 2") are now
removed before the number check. Result: 120 of 1,562 commitments are quantified (7.7%),
not 192 (12.3%). The 72 sentences that moved are all of the "by 2030, no figure" kind.
Regression tests for these cases are in `tests/test_classify.py`.

### Accuracy against hand labels: pending

`scripts/label_sample.py` drew 100 sentences (stratified by company and prediction) into
`eval/label_sample.csv`. Once the `label` column is filled with Q or V,
`python3 scripts/score_labels.py` writes precision and recall to `eval/label_results.md`.
Until then there is no accuracy number for this tool.

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
