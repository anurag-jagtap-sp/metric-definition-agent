"""Model IDs must come from GEMINI_*_MODEL env vars, never from source code."""

import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "metric-agent" / "metric_agent"
MODEL_ID = re.compile(r"""["'](gemini-|text-embedding-|models/gemini)[\w.\-]*["']""")


def test_no_model_ids_in_package_source():
    offenders = [
        f"{path.relative_to(PACKAGE)}:{number}"
        for path in PACKAGE.rglob("*.py")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if MODEL_ID.search(line)
    ]
    assert not offenders, f"hard-coded model IDs: {offenders}"
