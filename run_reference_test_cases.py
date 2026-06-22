"""Reference (golden) test-case runner for QuantumDigitalSignatureWithChannelNoise.

This script reads `reference_test_cases.json`, re-runs each saved input through
the current code, and compares the result against the saved expected output.

Why this exists: the JSON file stores a handful of known-good input/output pairs.
If the implementation is ever changed (refactor, optimization, bug fix), run this
script to confirm that the same inputs still produce the same outputs. Any
mismatch is reported field by field.

Usage:
    python run_reference_test_cases.py
    python run_reference_test_cases.py --update   # re-capture expected outputs

Exit code is 0 if all cases match, 1 otherwise (handy for CI).
"""

import argparse
import json
import math
import os
import sys

from quantum_digital_signature_channel_noise import (
    QuantumDigitalSignatureWithChannelNoise as QDS,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.join(HERE, "reference_test_cases.json")


def run_case(case):
    """Run one case and return the subset of result fields we compare."""
    qds = QDS(verbose=False, **case["input"])
    method = getattr(qds, case["method"])
    result = method()
    return {field: result[field] for field in case["expected_output"]}


def values_match(expected, actual, tol):
    if isinstance(expected, float) or isinstance(actual, float):
        try:
            return math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=tol)
        except (TypeError, ValueError):
            return False
    return expected == actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=DEFAULT_JSON, help="Path to the reference cases file.")
    parser.add_argument("--update", action="store_true", help="Overwrite expected outputs with freshly captured values.")
    args = parser.parse_args()

    with open(args.json, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    tol = float(data.get("float_tolerance", 1e-6))
    cases = data["cases"]

    if args.update:
        for case in cases:
            case["expected_output"] = run_case(case)
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        print(f"Updated expected outputs for {len(cases)} case(s) in {args.json}.")
        return 0

    total = len(cases)
    passed = 0
    print(f"Running {total} reference case(s) from {os.path.basename(args.json)}\n")

    for index, case in enumerate(cases, start=1):
        name = case["name"]
        expected = case["expected_output"]
        actual = run_case(case)

        mismatches = []
        for field, expected_value in expected.items():
            actual_value = actual.get(field)
            if not values_match(expected_value, actual_value, tol):
                mismatches.append((field, expected_value, actual_value))

        if not mismatches:
            passed += 1
            print(f"[{index}/{total}] PASS  {name}  ->  verdict={actual['verdict']}")
        else:
            print(f"[{index}/{total}] FAIL  {name}")
            for field, expected_value, actual_value in mismatches:
                print(f"           {field}: expected {expected_value!r}, got {actual_value!r}")

    print(f"\n{passed}/{total} reference cases passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
