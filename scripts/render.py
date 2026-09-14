"""Render cache/results.json into a single self-contained report.html.

No external assets, no CDN, no network calls at load time -- everything is
inlined so the file opens offline.
"""
import html
import json
import os

CACHE_PATH = "cache/results.json"
OUT_PATH = "report.html"

BAR_COLOR = "#5fd3a6"
BG = "#0b0d10"
PANEL = "#14181d"
TEXT = "#f2f4f6"
MUTED = "#9aa4ad"
QUANT_TAG = "#5fd3a6"
VAGUE_TAG = "#e0a35c"


def esc(s):
    return html.escape(s, quote=True)


def render_company_block(r):
    pct = r["quantified_pct"]
    rows = []
    for ex in r["report_examples"]:
        is_q = ex["label"] == "Quantified"
        tag_color = QUANT_TAG if is_q else VAGUE_TAG
        rows.append(f"""
        <tr>
          <td class="tag-cell"><span class="tag" style="background:{tag_color}22;color:{tag_color};border:1px solid {tag_color}66;">{esc(ex['label'])}</span></td>
          <td class="sentence-cell">{esc(ex['sentence'])}</td>
        </tr>""")

    return f"""
    <section class="company">
      <div class="company-head">
        <h2>{esc(r['display_name'])}</h2>
        <div class="pct">{pct:.1f}%<span class="pct-label"> quantified</span></div>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:{pct}%;"></div>
      </div>
      <div class="counts">{r['quantified_count']} quantified &middot; {r['vague_count']} vague &middot; {r['total']} total environmental commitments found</div>
      <table class="examples">
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>
    """


def render(results):
    results_sorted = sorted(results, key=lambda r: r["quantified_pct"], reverse=True)
    blocks = "\n".join(render_company_block(r) for r in results_sorted)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sustainability Commitment Classifier</title>
<style>
  :root {{
    color-scheme: dark;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: {BG};
    color: {TEXT};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    padding: 40px 24px 60px;
  }}
  .wrap {{
    max-width: 980px;
    margin: 0 auto;
  }}
  header h1 {{
    font-size: clamp(28px, 4vw, 44px);
    margin: 0 0 6px;
    letter-spacing: -0.01em;
  }}
  header p.sub {{
    color: {MUTED};
    font-size: clamp(15px, 2vw, 19px);
    margin: 0 0 36px;
    max-width: 760px;
    line-height: 1.5;
  }}
  .company {{
    background: {PANEL};
    border: 1px solid #ffffff14;
    border-radius: 14px;
    padding: 22px 24px 20px;
    margin-bottom: 22px;
  }}
  .company-head {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .company-head h2 {{
    font-size: clamp(22px, 3vw, 30px);
    margin: 0;
  }}
  .pct {{
    font-size: clamp(24px, 3vw, 32px);
    font-weight: 700;
    color: {BAR_COLOR};
  }}
  .pct-label {{
    font-size: 14px;
    font-weight: 400;
    color: {MUTED};
    margin-left: 4px;
  }}
  .bar-track {{
    width: 100%;
    height: 16px;
    background: #ffffff12;
    border-radius: 8px;
    margin-top: 14px;
    overflow: hidden;
  }}
  .bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, {BAR_COLOR}, #3fb98a);
    border-radius: 8px;
  }}
  .counts {{
    color: {MUTED};
    font-size: 13px;
    margin-top: 8px;
  }}
  table.examples {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 18px;
  }}
  table.examples td {{
    padding: 10px 0;
    border-top: 1px solid #ffffff10;
    vertical-align: top;
    font-size: 15px;
    line-height: 1.5;
  }}
  .tag-cell {{
    width: 118px;
    padding-right: 14px;
    white-space: nowrap;
  }}
  .tag {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
  }}
  .sentence-cell {{
    color: {TEXT};
  }}
  footer {{
    margin-top: 30px;
    color: {MUTED};
    font-size: 13px;
    border-top: 1px solid #ffffff14;
    padding-top: 18px;
    line-height: 1.6;
  }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Sustainability Commitment Classifier</h1>
      <p class="sub">Five DAX-listed companies, ranked by what share of their environmental
      commitments are checkable -- backed by a number and a target year -- versus vague.
      Sentences below are pulled directly from each company's own sustainability report.</p>
    </header>
    {blocks}
    <footer>
      A commitment counts as <strong>quantified</strong> when the sentence contains both a
      figure and a target year; otherwise it is <strong>vague</strong>. This is a rule-based
      check for whether a commitment is checkable -- it does not verify the numbers, and it
      is not a greenwashing detector. See README for method and known limitations.
    </footer>
  </div>
</body>
</html>
"""


def main():
    with open(CACHE_PATH, encoding="utf-8") as f:
        results = json.load(f)
    html_out = render(results)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Wrote {OUT_PATH} ({os.path.getsize(OUT_PATH)} bytes)")


if __name__ == "__main__":
    main()
