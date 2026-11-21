"""Draw a stratified sample of commitment sentences for hand labelling.

Writes eval/label_sample.csv: 20 sentences per company (10 predicted Quantified, 10 Vague
where available), in random order, with the prediction hidden in a separate file so the
labeller is not anchored by it. Fill in the `label` column with Q or V, then run
scripts/score_labels.py.
"""
import csv
import random
from pathlib import Path

import pipeline

ROOT = Path(__file__).resolve().parent.parent


def main(per_class: int = 10, seed: int = 26) -> None:
    rng = random.Random(seed)
    rows = []
    for company in pipeline.COMPANIES:
        r = pipeline.process_company(company)
        for kind, key in (("Quantified", "quantified_examples"), ("Vague", "vague_examples")):
            pool = sorted(set(r[key]))
            for s in rng.sample(pool, min(per_class, len(pool))):
                rows.append({"company": company, "sentence": s, "predicted": kind})
    rng.shuffle(rows)
    out = ROOT / "eval"
    out.mkdir(exist_ok=True)
    with open(out / "label_sample.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "company", "sentence", "label"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r["company"], r["sentence"], ""])
    with open(out / "label_sample_predictions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "predicted"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r["predicted"]])
    print(f"wrote {len(rows)} sentences to eval/label_sample.csv")


if __name__ == "__main__":
    import os
    os.chdir(ROOT)
    main()
