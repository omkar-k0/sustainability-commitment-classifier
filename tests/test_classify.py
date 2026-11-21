import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from pipeline import classify, filter_commitments  # noqa: E402

QUANTIFIED = [
    "We will cut emissions by 42% by 2030 versus 2019.",
    "Scope 1, 2 and 3 emissions will be reduced by 30 percent by 2035.",
    "We will save 1.2 million tonnes of CO2 by 2030.",
    "By 2030 we aim to reach 500 GWh of renewable energy.",
]
VAGUE = [
    # a target year alone is not a figure (this was counted as Quantified before 21 Nov 2026)
    "We will reduce our emissions significantly by 2030.",
    # scope labels are not figures
    "We aim to reduce Scope 1 and 2 emissions by 2030.",
    "The increase in energy efficiency will contribute to the Scope 1 and Scope 2 targets for 2030.",
    # a baseline year is not a figure either
    "Compared with 2019, we will lower emissions further by 2030.",
    # a figure without a target year
    "We plan to source 100% renewable electricity.",
]


def test_quantified():
    for s in QUANTIFIED:
        assert classify(s) == "Quantified", s


def test_vague():
    for s in VAGUE:
        assert classify(s) == "Vague", s


def test_filter_needs_forward_looking_and_environmental():
    kept = filter_commitments([
        "We will reduce water use at all sites by 2030.",       # both
        "Our water use fell last year at most sites overall.",  # no forward-looking marker
        "We will hire 2,000 engineers in the coming years.",    # not environmental
    ])
    assert kept == ["We will reduce water use at all sites by 2030."]


def test_headline_numbers_are_reproducible(monkeypatch):
    import pipeline
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    results = [pipeline.process_company(c) for c in pipeline.COMPANIES]
    total = sum(r["total"] for r in results)
    quantified = sum(r["quantified_count"] for r in results)
    assert total == 1562
    assert quantified == 120
