#!/usr/bin/env python3
"""
E2E Test Runner for Joblet MCP Server

This script provides a convenient way to run end-to-end tests with different
configurations and environments.
"""

import argparse
import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_prerequisites():
    """Check if required tools are available"""
    print("Checking prerequisites...")

    # Check for rnx binary
    rnx_path = shutil.which("rnx")
    if not rnx_path:
        print("❌ rnx binary not found in PATH")
        print("   Please install rnx or add it to your PATH")
        return False
    else:
        print(f"✅ rnx found at: {rnx_path}")

    # Check rnx version
    try:
        result = subprocess.run(
            ["rnx", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ rnx version: {result.stdout.strip()}")
        else:
            print(f"⚠️  rnx version check failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not check rnx version: {e}")

    # Check if joblet server is reachable
    try:
        result = subprocess.run(
            ["rnx", "node", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Joblet server connection successful")
        else:
            print(f"⚠️  Joblet server connection failed: {result.stderr}")
            print("   Some tests may be skipped")
            print("   Make sure ~/.rnx/rnx-config.yml is properly configured with embedded TLS certificates")
    except Exception as e:
        print(f"⚠️  Could not test Joblet server connection: {e}")
        print("   Some tests may be skipped")
        print("   Ensure rnx configuration is set up with embedded certificates at ~/.rnx/rnx-config.yml")

    return True


def run_tests(test_type="all", verbose=False, markers=None, parallel=False):
    """Run the e2e tests"""
    project_root = Path(__file__).parent.parent

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test paths based on type
    if test_type == "all":
        cmd.append("tests/e2e/")
    elif test_type == "quick":
        cmd.extend(["tests/e2e/", "-m", "not slow"])
    elif test_type == "job":
        cmd.append("tests/e2e/test_job_management.py")
    elif test_type == "resource":
        cmd.append("tests/e2e/test_resource_management.py")
    elif test_type == "runtime":
        cmd.append("tests/e2e/test_runtimes.py")
    else:
        cmd.append(f"tests/e2e/{test_type}")

    # Add markers if specified
    if markers:
        cmd.extend(["-m", markers])

    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Add parallel execution if requested
    if parallel and shutil.which("pytest-xdist"):
        cmd.extend(["-n", "auto"])

    # Add other useful flags
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])

    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)

    # Change to project directory
    os.chdir(project_root)

    # Run tests
    try:
        result = subprocess.run(cmd, env=os.environ.copy())
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1


def list_available_tests():
    """List available test files and their descriptions"""
    project_root = Path(__file__).parent.parent
    e2e_dir = project_root / "tests" / "e2e"

    if not e2e_dir.exists():
        print("E2E test directory not found")
        return

    print("Available E2E Tests:")
    print("=" * 50)

    test_files = {
        "test_job_management.py": "Basic job operations: run, monitor, cancel, delete",
        "test_resource_management.py": "Volume and network management, system monitoring",
        "test_runtimes.py": "Runtime-specific tests for Python, Java, ML workflows"
    }

    for test_file, description in test_files.items():
        test_path = e2e_dir / test_file
        if test_path.exists():
            print(f"📁 {test_file}")
            print(f"   {description}")

            # Try to extract test classes/methods
            try:
                with open(test_path) as f:
                    content = f.read()
                    import re
                    classes = re.findall(r'class (Test\w+)', content)
                    if classes:
                        print(f"   Classes: {', '.join(classes)}")
            except Exception:
                pass
            print()

    print("Test Types:")
    print("-" * 20)
    print("all      - Run all e2e tests")
    print("quick    - Run non-slow tests only")
    print("job      - Job management tests only")
    print("resource - Resource management tests only")
    print("runtime  - Runtime-specific tests only")


def main():
    parser = argparse.ArgumentParser(
        description="Run Joblet MCP Server E2E Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run-e2e-tests.py --check
  python scripts/run-e2e-tests.py --type quick
  python scripts/run-e2e-tests.py --type runtime --verbose
  python scripts/run-e2e-tests.py --markers "not slow"
  python scripts/run-e2e-tests.py --list
        """
    )

    parser.add_argument(
        "--type", "-t",
        default="all",
        choices=["all", "quick", "job", "resource", "runtime"],
        help="Type of tests to run"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Check prerequisites only"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available tests"
    )

    parser.add_argument(
        "--markers", "-m",
        help="Pytest markers to apply (e.g., 'not slow')"
    )

    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )

    args = parser.parse_args()

    if args.list:
        list_available_tests()
        return 0

    if args.check:
        if check_prerequisites():
            print("\n✅ All prerequisites met")
            return 0
        else:
            print("\n❌ Prerequisites not met")
            return 1

    # Check prerequisites before running tests
    if not check_prerequisites():
        print("\n⚠️  Some prerequisites not met, but continuing with tests...")
        print("   Some tests may be skipped\n")

    # Run tests
    return run_tests(
        test_type=args.type,
        verbose=args.verbose,
        markers=args.markers,
        parallel=args.parallel
    )


if __name__ == "__main__":
    sys.exit(main())