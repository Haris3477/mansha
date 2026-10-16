"""Re-check saved pipeline runs with the automatic report check (Step 9.6b). No LLM, no router.

Run (from the project root):
    python -m scripts.check_reports                                   # every run in runs/pipeline/
    python -m scripts.check_reports runs/pipeline/20261016-184437_windows [...]

For each run folder with a report.md it reads report.md, evidence.txt, message.txt, the
last researcher_N.json (the accepted round) and intake.json (language), and prints the
problems and warnings. Folders with a notice.md (stops) are listed and skipped: their
text is written by code. Exit code 1 if any report has a problem.
"""

import argparse
import json
import sys
from pathlib import Path

from mansha.report_check import check_report

RUNS_ROOT = Path("runs/pipeline")


def check_folder(folder: Path) -> tuple[list[str], list[str]] | None:
    """(problems, warnings) for one run folder, or None if it has no report."""
    if not (folder / "report.md").exists():
        return None
    rounds = sorted(folder.glob("researcher_*.json"))
    research = json.loads(rounds[-1].read_text(encoding="utf-8"))["output"]
    intake = json.loads((folder / "intake.json").read_text(encoding="utf-8"))["output"]
    return check_report((folder / "report.md").read_text(encoding="utf-8"), research=research,
                        evidence_text=(folder / "evidence.txt").read_text(encoding="utf-8"),
                        message=(folder / "message.txt").read_text(encoding="utf-8"),
                        language=intake.get("language") or "en")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Re-check saved Mansha reports.")
    parser.add_argument("folders", nargs="*", help="run folders (default: all in runs/pipeline/)")
    args = parser.parse_args(argv)
    folders = [Path(f) for f in args.folders] or sorted(p for p in RUNS_ROOT.iterdir() if p.is_dir())

    flagged = 0
    for folder in folders:
        result = check_folder(folder)
        if result is None:
            print(f"-     {folder.name}  (no report.md: a stop, skipped)")
            continue
        problems, warnings = result
        flagged += bool(problems)
        tag = "FLAG " if problems else ("WARN " if warnings else "OK   ")
        print(f"{tag} {folder.name}  {len(problems)} problem(s), {len(warnings)} warning(s)")
        for x in problems:
            print(f"        problem: {x}")
        for x in warnings:
            print(f"        warning: {x}")
    print(f"\n{flagged} report(s) with problems. The check reads form, not meaning: still read each report.")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
