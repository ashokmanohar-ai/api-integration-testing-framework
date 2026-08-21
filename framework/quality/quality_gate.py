"""Configurable release gate over JUnit XML."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GateResult:
    total: int
    failures: int
    errors: int
    skipped: int

    @property
    def executed(self) -> int:
        return self.total - self.skipped

    @property
    def passed(self) -> int:
        return self.executed - self.failures - self.errors

    @property
    def pass_rate(self) -> float:
        return 100.0 if not self.executed else self.passed / self.executed * 100


def parse_junit(path: Path) -> GateResult:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    return GateResult(
        total=sum(int(suite.attrib.get("tests", 0)) for suite in suites),
        failures=sum(int(suite.attrib.get("failures", 0)) for suite in suites),
        errors=sum(int(suite.attrib.get("errors", 0)) for suite in suites),
        skipped=sum(int(suite.attrib.get("skipped", 0)) for suite in suites),
    )


def render_decision(result: GateResult, threshold: float) -> tuple[str, bool]:
    passed = result.pass_rate >= threshold and result.failures == 0 and result.errors == 0
    decision = "PASS" if passed else "FAIL"
    output = (
        "QUALITY GATE\n\n"
        f"Executed:          {result.executed}\n"
        f"Passed:            {result.passed}\n"
        f"Failures:          {result.failures}\n"
        f"Errors:            {result.errors}\n"
        f"Skipped:           {result.skipped}\n"
        f"Pass Rate:         {result.pass_rate:.2f}%\n"
        f"Required:          {threshold:.2f}%\n\n"
        f"RELEASE DECISION: {decision}"
    )
    return output, passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=100.0)
    args = parser.parse_args()
    output, passed = render_decision(parse_junit(args.junit), args.threshold)
    print(output)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
