"""Summarize behave's JUnit XML as Markdown for the GitHub Actions job summary.

python scripts/junit_summary.py reports/junit >> "$GITHUB_STEP_SUMMARY"
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MESSAGE_LIMIT = 200  # characters of each failure message to show


def _cell(text):
    # One line per table row, and a "|" in the text must not start a new column
    text = " ".join(text.split()).replace("|", "\\|")
    return text if len(text) <= MESSAGE_LIMIT else text[:MESSAGE_LIMIT] + "..."


def _problem(case):
    """(location, message) for a scenario that didn't pass."""
    problem = case.find("failure")
    if problem is None:
        problem = case.find("error")
    if problem is None:
        return "", case.get("status", "")
    location = re.search(r"^Location: (\S+)", problem.text or "", re.MULTILINE)
    return (location.group(1) if location else ""), problem.get("message", "")


def summarize(directory):
    paths = sorted(Path(directory).glob("*.xml"))
    if not paths:
        return f"No JUnit results in `{directory}`: the run stopped before any scenario.\n"

    rows, failures = [], []
    for path in paths:
        suite = ET.parse(path).getroot()
        passed = failed = not_run = 0
        # Count each scenario's own status: when a feature hook fails, behave marks the
        # scenarios "untested" but still reports failures="0" on the suite
        for case in suite.iter("testcase"):
            status = case.get("status")
            if status == "passed":
                passed += 1
            elif status == "untested":
                not_run += 1
            elif status != "skipped":  # skipped = left out by the tag filter
                failed += 1
                failures.append((case.get("name", ""), *_problem(case)))
        rows.append((suite.get("name", path.stem), passed, failed, not_run, float(suite.get("time", 0))))

    total = [sum(row[i] for row in rows) for i in range(1, 5)]
    heading = f"### Scenarios: {total[0]} passed, {total[1]} failed"
    lines = [
        heading + (f", {total[2]} not run" if total[2] else ""),
        "",
        "| Feature | Passed | Failed | Not run | Time |",
        "|---|---:|---:|---:|---:|",
    ]
    lines += [
        f"| `{name}` | {passed} | {failed} | {not_run} | {seconds:.1f} s |"
        for name, passed, failed, not_run, seconds in rows
    ]
    lines.append("| **Total** | **{}** | **{}** | **{}** | **{:.1f} s** |".format(*total))

    if failures:
        lines += ["", "#### Failed scenarios", "", "| Scenario | Location | Message |", "|---|---|---|"]
        lines += [
            f"| {_cell(name)} | `{location}` | {_cell(message)} |"
            if location
            else f"| {_cell(name)} | | {_cell(message)} |"
            for name, location, message in failures
        ]
    if total[2]:
        lines += [
            "",
            "Scenarios that did not run were usually stopped by a failing hook, "
            "such as the `@authenticated` login; the job log shows the error.",
        ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(summarize(sys.argv[1] if len(sys.argv) > 1 else "reports/junit"))
