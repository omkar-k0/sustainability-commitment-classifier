"""
Sustainability commitment classifier pipeline.

Reads cached plain text per company (data/<company>.txt), segments into
sentences, filters to forward-looking commitment sentences, classifies each
as Quantified (has a number AND a target year) or Vague, aggregates counts,
and renders a single offline report.html.

This is a rule-based (regex) classifier. It does not use any LLM, embedding,
or model inference. See README.md for the method and its known weaknesses.
"""
import json
import os
import re

DATA_DIR = "data"
CACHE_DIR = "cache"
COMPANIES = ["siemens", "basf", "sap", "henkel", "bosch"]
DISPLAY_NAMES = {
    "siemens": "Siemens",
    "basf": "BASF",
    "sap": "SAP",
    "henkel": "Henkel",
    "bosch": "Bosch",
}

MIN_SENT_LEN = 40
MAX_SENT_LEN = 400

FORWARD_LOOKING_MARKERS = [
    r"\bwill\b",
    r"\baim(?:s|ing|ed)?\b",
    r"\btarget(?:s|ed|ing)?\b",
    r"\bplan(?:s|ned|ning)?\b",
    r"\bcommit(?:s|ted|ting|ment)?\b",
    r"\bintend(?:s|ed|ing)?\b",
    r"\bby\s+20\d{2}\b",
    r"\breduc(?:e|es|ed|ing|tion)\b",
    r"\bachiev(?:e|es|ed|ing)\b",
    r"\bgoal(?:s)?\b",
]
FORWARD_LOOKING_RE = re.compile("|".join(FORWARD_LOOKING_MARKERS), re.IGNORECASE)

# The captain's brief asks specifically for *environmental* commitments (not
# HR/financial/governance ones that also happen to contain words like
# "target" or "plan"). This is a second regex gate on top of the
# forward-looking filter -- still pure keyword matching, no model.
ENVIRONMENTAL_TOPIC_MARKERS = [
    r"emission", r"\bCO2?e?\b", r"climate", r"carbon", r"\benergy\b",
    r"renewable", r"\bwater\b", r"\bwaste\b", r"circular", r"biodivers",
    r"environment", r"\bGHG\b", r"scope\s*[123]", r"sustainab",
    r"recycl", r"pollution", r"\bnet.zero\b", r"greenhouse",
    r"deforestation", r"resource", r"decarboniz",
]
ENVIRONMENTAL_TOPIC_RE = re.compile("|".join(ENVIRONMENTAL_TOPIC_MARKERS), re.IGNORECASE)

# has-a-number: a percentage, a figure with a recognized unit, or a plain
# integer greater than 1 (avoids matching lone "a" or "1" article-like tokens).
NUMBER_RE = re.compile(
    r"""
    \d+(?:[.,]\d+)?\s*%                                   # percentage
    | \d+(?:[.,]\d+)?\s*(?:t\s?CO2e?|tCO2e?|MWh|GWh|kWh|MtCO2e?|tonnes?|tons?|kg|km|EUR|€|\$)  # unit figure
    | \b(?:[2-9]|[1-9]\d+)\b                              # plain integer > 1
    """,
    re.IGNORECASE | re.VERBOSE,
)

# has-a-year: a target year pattern, 2025-2050.
YEAR_RE = re.compile(r"\b20(?:2[5-9]|[3-4]\d|50)\b")


def strip_repeated_lines(text, min_repeats=5):
    """Drop lines (page headers/footers, repeated running titles) that recur
    on many pages -- these are not sentence content and otherwise pollute
    the segmented output with jumbled artifacts."""
    lines = text.split("\n")
    counts = {}
    for line in lines:
        key = line.strip()
        if key:
            counts[key] = counts.get(key, 0) + 1
    kept = [line for line in lines if counts.get(line.strip(), 0) < min_repeats]
    return "\n".join(kept)


def segment(text):
    text = strip_repeated_lines(text)
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    sentences = []
    for s in raw_sentences:
        s = re.sub(r"\s+", " ", s).strip()
        if MIN_SENT_LEN <= len(s) <= MAX_SENT_LEN:
            sentences.append(s)
    return sentences


def filter_commitments(sentences):
    return [
        s for s in sentences
        if FORWARD_LOOKING_RE.search(s) and ENVIRONMENTAL_TOPIC_RE.search(s)
    ]


def legibility_score(sentence):
    """Rough proxy for how readable a sentence is, used only to pick which
    example sentences to display in the report. PDF column extraction
    sometimes interleaves unrelated text; shorter, mostly-alphabetic
    sentences without stray table fragments tend to read cleanly."""
    length_penalty = abs(len(sentence) - 140)
    alpha_chars = sum(c.isalpha() or c.isspace() for c in sentence)
    alpha_ratio = alpha_chars / max(1, len(sentence))
    digit_clusters = len(re.findall(r"\d{3,}", sentence))
    starts_capital = sentence[:1].isupper()
    ends_period = sentence.rstrip().endswith(".")
    boundary_bonus = 0 if starts_capital else 40
    boundary_bonus += 0 if ends_period else 20
    # A hyphen followed by a space usually marks a line-wrapped word that
    # got interleaved with unrelated column text during PDF extraction --
    # a strong signal this sentence will read as garbled.
    broken_word_penalty = len(re.findall(r"\w-\s", sentence)) * 60
    return (
        length_penalty - alpha_ratio * 100 + digit_clusters * 30
        + boundary_bonus + broken_word_penalty
    )


def pick_report_examples(quantified, vague, n=3):
    """Pick a mix of quantified and vague example sentences for the report,
    favoring the most legible ones. At least one of each kind when both
    exist."""
    quantified = list(dict.fromkeys(quantified))
    vague = list(dict.fromkeys(vague))
    q_sorted = sorted(quantified, key=legibility_score)
    v_sorted = sorted(vague, key=legibility_score)
    picks = []
    if q_sorted:
        picks.append(q_sorted[0])
    if v_sorted:
        picks.append(v_sorted[0])
    remaining = sorted(q_sorted[1:] + v_sorted[1:], key=legibility_score)
    for s in remaining:
        if len(picks) >= n:
            break
        picks.append(s)
    return picks[:n]


def classify(sentence):
    has_number = bool(NUMBER_RE.search(sentence))
    has_year = bool(YEAR_RE.search(sentence))
    if has_number and has_year:
        return "Quantified"
    return "Vague"


def load_text(company):
    path = os.path.join(DATA_DIR, f"{company}.txt")
    with open(path, encoding="utf-8") as f:
        return f.read()


def process_company(company):
    text = load_text(company)
    sentences = segment(text)
    commitments = filter_commitments(sentences)
    classified = [(s, classify(s)) for s in commitments]
    quantified = [s for s, c in classified if c == "Quantified"]
    vague = [s for s, c in classified if c == "Vague"]
    total = len(classified)
    pct = round(100 * len(quantified) / total, 1) if total else 0.0
    return {
        "company": company,
        "display_name": DISPLAY_NAMES[company],
        "total": total,
        "quantified_count": len(quantified),
        "vague_count": len(vague),
        "quantified_pct": pct,
        "quantified_examples": quantified,
        "vague_examples": vague,
        "report_examples": [
            {"sentence": s, "label": classify(s)}
            for s in pick_report_examples(quantified, vague, n=3)
        ],
    }


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    results = []
    for company in COMPANIES:
        r = process_company(company)
        results.append(r)
        print(
            f"{r['display_name']:12s} total={r['total']:4d}  "
            f"quantified={r['quantified_count']:4d}  vague={r['vague_count']:4d}  "
            f"quantified%={r['quantified_pct']:5.1f}%"
        )

    cache_path = os.path.join(CACHE_DIR, "results.json")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nCached aggregate results to {cache_path}")
    return results


if __name__ == "__main__":
    main()
