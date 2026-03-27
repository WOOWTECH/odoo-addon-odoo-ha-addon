"""
Test Report Generator for Stability Testing

Collects test results and generates JSON + text reports.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

_logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")


class TestResult:
    """Single test case result."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

    def __init__(self, test_id: str, name: str, category: str):
        self.test_id = test_id
        self.name = name
        self.category = category
        self.status = None
        self.message = ""
        self.details = {}
        self.duration = 0.0
        self._start_time = None

    def start(self):
        self._start_time = time.time()

    def passed(self, message: str = ""):
        self.status = self.PASS
        self.message = message
        self._finish()

    def failed(self, message: str, details: dict = None):
        self.status = self.FAIL
        self.message = message
        self.details = details or {}
        self._finish()

    def skipped(self, reason: str = ""):
        self.status = self.SKIP
        self.message = reason
        self._finish()

    def errored(self, message: str, details: dict = None):
        self.status = self.ERROR
        self.message = message
        self.details = details or {}
        self._finish()

    def _finish(self):
        if self._start_time:
            self.duration = time.time() - self._start_time

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "duration_s": round(self.duration, 3),
        }


class TestReport:
    """Aggregate test report for a round of testing."""

    def __init__(self, round_id: str, description: str):
        self.round_id = round_id
        self.description = description
        self.results: list[TestResult] = []
        self.start_time = None
        self.end_time = None
        self.metadata = {}

    def start(self):
        self.start_time = datetime.now(timezone.utc)

    def finish(self):
        self.end_time = datetime.now(timezone.utc)

    def add_result(self, result: TestResult):
        self.results.append(result)

    def new_test(self, test_id: str, name: str, category: str) -> TestResult:
        """Create, register, and return a new TestResult."""
        result = TestResult(test_id, name, category)
        self.results.append(result)
        return result

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == TestResult.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == TestResult.FAIL)

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.status == TestResult.ERROR)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == TestResult.SKIP)

    @property
    def pass_rate(self) -> float:
        executed = self.total - self.skipped
        if executed == 0:
            return 0.0
        return (self.passed / executed) * 100

    @property
    def total_duration(self) -> float:
        return sum(r.duration for r in self.results)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def summary_dict(self) -> dict:
        return {
            "round": self.round_id,
            "description": self.description,
            "started": self.start_time.isoformat() if self.start_time else None,
            "finished": self.end_time.isoformat() if self.end_time else None,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "pass_rate": round(self.pass_rate, 1),
            "total_duration_s": round(self.total_duration, 1),
            "metadata": self.metadata,
        }

    def to_dict(self) -> dict:
        return {
            **self.summary_dict(),
            "results": [r.to_dict() for r in self.results],
        }

    def save_json(self, filename: str = None) -> str:
        """Save report as JSON. Returns file path."""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        filename = filename or f"{self.round_id}.json"
        path = os.path.join(REPORTS_DIR, filename)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        _logger.info(f"JSON report saved: {path}")
        return path

    def save_text(self, filename: str = None) -> str:
        """Save report as human-readable text. Returns file path."""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        filename = filename or f"{self.round_id}.txt"
        path = os.path.join(REPORTS_DIR, filename)

        lines = [
            f"{'=' * 70}",
            f"  STABILITY TEST REPORT — {self.round_id.upper()}",
            f"  {self.description}",
            f"{'=' * 70}",
            f"",
            f"  Started:  {self.start_time.isoformat() if self.start_time else 'N/A'}",
            f"  Finished: {self.end_time.isoformat() if self.end_time else 'N/A'}",
            f"  Duration: {self.total_duration:.1f}s",
            f"",
            f"  Total: {self.total}  |  "
            f"PASS: {self.passed}  |  FAIL: {self.failed}  |  "
            f"ERROR: {self.errors}  |  SKIP: {self.skipped}",
            f"  Pass Rate: {self.pass_rate:.1f}%",
            f"{'=' * 70}",
            f"",
        ]

        # Group by category
        categories = {}
        for r in self.results:
            categories.setdefault(r.category, []).append(r)

        for cat, results in categories.items():
            cat_pass = sum(1 for r in results if r.status == TestResult.PASS)
            cat_total = len(results)
            lines.append(f"--- {cat} ({cat_pass}/{cat_total}) ---")
            for r in results:
                icon = {
                    TestResult.PASS: "PASS",
                    TestResult.FAIL: "FAIL",
                    TestResult.SKIP: "SKIP",
                    TestResult.ERROR: "ERR!",
                }.get(r.status, "????")
                line = f"  [{icon}] {r.test_id}: {r.name}"
                if r.duration > 0:
                    line += f" ({r.duration:.1f}s)"
                lines.append(line)
                if r.status in (TestResult.FAIL, TestResult.ERROR):
                    lines.append(f"         -> {r.message}")
                    if r.details:
                        for k, v in r.details.items():
                            detail_str = str(v)
                            if len(detail_str) > 200:
                                detail_str = detail_str[:200] + "..."
                            lines.append(f"            {k}: {detail_str}")
            lines.append("")

        # Failure summary
        failures = [r for r in self.results
                     if r.status in (TestResult.FAIL, TestResult.ERROR)]
        if failures:
            lines.append(f"{'=' * 70}")
            lines.append(f"  FAILURES & ERRORS ({len(failures)})")
            lines.append(f"{'=' * 70}")
            for r in failures:
                lines.append(f"  [{r.status}] {r.test_id}: {r.message}")
            lines.append("")

        with open(path, "w") as f:
            f.write("\n".join(lines))
        _logger.info(f"Text report saved: {path}")
        return path

    def print_summary(self):
        """Print summary to stdout."""
        status = "PASS" if self.failed == 0 and self.errors == 0 else "FAIL"
        print(f"\n{'=' * 60}")
        print(f"  {self.round_id.upper()}: {status}")
        print(f"  Total: {self.total} | PASS: {self.passed} | "
              f"FAIL: {self.failed} | ERROR: {self.errors} | "
              f"SKIP: {self.skipped}")
        print(f"  Pass Rate: {self.pass_rate:.1f}% | "
              f"Duration: {self.total_duration:.1f}s")
        print(f"{'=' * 60}")

        failures = [r for r in self.results
                     if r.status in (TestResult.FAIL, TestResult.ERROR)]
        if failures:
            print(f"\n  Failures:")
            for r in failures:
                print(f"    [{r.status}] {r.test_id}: {r.message}")
        print()


class MasterReport:
    """Aggregate report across all rounds."""

    def __init__(self):
        self.rounds: list[TestReport] = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = datetime.now(timezone.utc)

    def finish(self):
        self.end_time = datetime.now(timezone.utc)

    def add_round(self, report: TestReport):
        self.rounds.append(report)

    @property
    def total(self) -> int:
        return sum(r.total for r in self.rounds)

    @property
    def passed(self) -> int:
        return sum(r.passed for r in self.rounds)

    @property
    def failed(self) -> int:
        return sum(r.failed for r in self.rounds)

    @property
    def errors(self) -> int:
        return sum(r.errors for r in self.rounds)

    @property
    def pass_rate(self) -> float:
        skipped = sum(r.skipped for r in self.rounds)
        executed = self.total - skipped
        if executed == 0:
            return 0.0
        return (self.passed / executed) * 100

    def save_all(self) -> str:
        """Save master report + all round reports. Returns master path."""
        os.makedirs(REPORTS_DIR, exist_ok=True)

        # Save individual rounds
        for r in self.rounds:
            r.save_json()
            r.save_text()

        # Save master
        master = {
            "started": self.start_time.isoformat() if self.start_time else None,
            "finished": self.end_time.isoformat() if self.end_time else None,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "pass_rate": round(self.pass_rate, 1),
            "rounds": [r.summary_dict() for r in self.rounds],
        }
        path = os.path.join(REPORTS_DIR, "master_report.json")
        with open(path, "w") as f:
            json.dump(master, f, indent=2, ensure_ascii=False)

        # Text summary
        txt_path = os.path.join(REPORTS_DIR, "master_report.txt")
        lines = [
            f"{'=' * 70}",
            f"  MASTER STABILITY TEST REPORT",
            f"{'=' * 70}",
            f"  Started:  {self.start_time.isoformat() if self.start_time else 'N/A'}",
            f"  Finished: {self.end_time.isoformat() if self.end_time else 'N/A'}",
            f"",
            f"  Total: {self.total} | PASS: {self.passed} | "
            f"FAIL: {self.failed} | ERROR: {self.errors}",
            f"  Pass Rate: {self.pass_rate:.1f}%",
            f"{'=' * 70}",
            f"",
        ]
        for r in self.rounds:
            status = "PASS" if r.failed == 0 and r.errors == 0 else "FAIL"
            lines.append(
                f"  [{status}] {r.round_id}: "
                f"{r.passed}/{r.total} passed ({r.pass_rate:.0f}%) "
                f"in {r.total_duration:.1f}s"
            )
        lines.append("")

        with open(txt_path, "w") as f:
            f.write("\n".join(lines))

        _logger.info(f"Master report saved: {path}")
        return path

    def print_summary(self):
        """Print master summary."""
        status = "PASS" if self.failed == 0 and self.errors == 0 else "FAIL"
        print(f"\n{'#' * 60}")
        print(f"  MASTER REPORT: {status}")
        print(f"  Total: {self.total} | PASS: {self.passed} | "
              f"FAIL: {self.failed} | ERROR: {self.errors}")
        print(f"  Pass Rate: {self.pass_rate:.1f}%")
        print(f"{'#' * 60}")
        for r in self.rounds:
            s = "PASS" if r.failed == 0 and r.errors == 0 else "FAIL"
            print(f"  [{s}] {r.round_id}: "
                  f"{r.passed}/{r.total} ({r.pass_rate:.0f}%)")
        print()
