#!/usr/bin/env python3
"""
E2E Test Runner for Entity Controller Tests

This script provides a convenient way to run E2E tests with various options.

Usage:
    # Run all tests
    python e2e_tests/run_tests.py

    # Run specific domain tests
    python e2e_tests/run_tests.py --domain switch
    python e2e_tests/run_tests.py --domain light

    # Run in headed mode (visible browser)
    python e2e_tests/run_tests.py --headed

    # Run with slow motion (for debugging)
    python e2e_tests/run_tests.py --slow-mo 500

    # Generate HTML report
    python e2e_tests/run_tests.py --html-report

    # Run with custom config
    python e2e_tests/run_tests.py --config my_config.yaml
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


# Available domains
DOMAINS = [
    "switch",
    "light",
    "sensor",
    "climate",
    "cover",
    "fan",
    "automation",
    "scene",
    "script",
]


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Run E2E tests for entity controllers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run all tests
    python run_tests.py

    # Run only switch tests
    python run_tests.py --domain switch

    # Run multiple domains
    python run_tests.py --domain switch --domain light

    # Debug mode (headed + slow)
    python run_tests.py --debug

    # Generate HTML report
    python run_tests.py --html-report
        """,
    )

    parser.add_argument(
        "--domain",
        action="append",
        choices=DOMAINS,
        help="Run tests for specific domain(s). Can be specified multiple times.",
    )

    parser.add_argument(
        "--all-domains",
        action="store_true",
        help="Run tests for all domains",
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (visible)",
    )

    parser.add_argument(
        "--slow-mo",
        type=int,
        default=0,
        help="Slow down browser actions by X milliseconds",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode: headed browser with 500ms slow-mo",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to E2E config YAML file",
    )

    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report",
    )

    parser.add_argument(
        "--json-report",
        action="store_true",
        help="Generate JSON test report",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    parser.add_argument(
        "-x", "--exitfirst",
        action="store_true",
        help="Exit on first failure",
    )

    parser.add_argument(
        "-k",
        type=str,
        help="Only run tests matching expression (pytest -k)",
    )

    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Run tests in parallel with N workers",
    )

    return parser.parse_args()


def build_pytest_command(args):
    """Build pytest command from arguments"""
    cmd = ["python", "-m", "pytest", "e2e_tests/"]

    # Verbose output
    if args.verbose:
        cmd.append("-v")

    # Exit on first failure
    if args.exitfirst:
        cmd.append("-x")

    # Domain filter
    if args.domain:
        markers = " or ".join(f"domain_{d}" for d in args.domain)
        cmd.extend(["-m", markers])

    # Keyword expression
    if args.k:
        cmd.extend(["-k", args.k])

    # Debug mode
    if args.debug:
        args.headed = True
        args.slow_mo = 500

    # Browser options
    if args.headed:
        cmd.append("--headless=false")
    else:
        cmd.append("--headless=true")

    if args.slow_mo:
        cmd.extend(["--slow-mo", str(args.slow_mo)])

    # Config file
    if args.config:
        cmd.extend(["--config-file", args.config])

    # Reports
    report_dir = Path("e2e_tests/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    if args.html_report:
        cmd.extend(["--html", str(report_dir / "report.html"), "--self-contained-html"])

    if args.json_report:
        cmd.extend(["--json-report", f"--json-report-file={report_dir / 'report.json'}"])

    # Parallel execution
    if args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])

    return cmd


def check_dependencies():
    """Check if required dependencies are installed"""
    required = ["pytest", "playwright", "yaml"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print("Missing dependencies:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstall with:")
        print("  pip install pytest playwright pyyaml")
        if "playwright" in missing:
            print("  playwright install chromium")
        return False

    return True


def check_browser():
    """Check if Playwright browser is installed"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
        return True
    except Exception as e:
        print(f"Browser not available: {e}")
        print("\nInstall Playwright browser:")
        print("  playwright install chromium")
        return False


def main():
    """Main entry point"""
    args = parse_args()

    # Change to project directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check browser
    if not check_browser():
        sys.exit(1)

    # Build and run pytest command
    cmd = build_pytest_command(args)

    print("Running command:")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
