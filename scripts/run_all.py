"""Run the full pipeline: extract -> classify/aggregate -> render report.html."""
import subprocess
import sys

STEPS = ["scripts/extract.py", "scripts/pipeline.py", "scripts/render.py"]

for step in STEPS:
    print(f"\n=== {step} ===")
    result = subprocess.run([sys.executable, step])
    if result.returncode != 0:
        sys.exit(result.returncode)
