"""Score the classifier against your hand labels in eval/label_sample.csv.

Label column: Q = the sentence names a figure and a target year for an environmental
commitment, V = it does not. Leave a row blank to skip it. Writes eval/label_results.md.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    labels = {r["id"]: r["label"].strip().upper() for r in csv.DictReader(open(ROOT / "eval/label_sample.csv", encoding="utf-8"))}
    preds = {r["id"]: r["predicted"] for r in csv.DictReader(open(ROOT / "eval/label_sample_predictions.csv", encoding="utf-8"))}
    pairs = [(preds[i], "Quantified" if l == "Q" else "Vague") for i, l in labels.items() if l in ("Q", "V")]
    if not pairs:
        raise SystemExit("No labels yet: fill the label column with Q or V.")
    n = len(pairs)
    acc = sum(p == t for p, t in pairs) / n
    tp = sum(p == t == "Quantified" for p, t in pairs)
    pred_q = sum(p == "Quantified" for p, _ in pairs)
    true_q = sum(t == "Quantified" for _, t in pairs)
    lines = [
        "# Hand-label evaluation",
        "",
        f"Labelled sentences: {n} (stratified: up to 10 predicted Quantified and 10 predicted Vague per company)",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Accuracy | {acc:.1%} |",
        f"| Precision of Quantified | {tp / pred_q:.1%} ({tp} of {pred_q}) |" if pred_q else "| Precision of Quantified | n/a |",
        f"| Recall of Quantified | {tp / true_q:.1%} ({tp} of {true_q}) |" if true_q else "| Recall of Quantified | n/a |",
        "",
        "The sample is stratified by prediction, so accuracy here is not the accuracy on all 1,562 sentences.",
    ]
    (ROOT / "eval/label_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
