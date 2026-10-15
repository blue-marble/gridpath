# Copyright 2026 Sylvan Energy Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Build the model for every scenario directory under a location (the examples
directory by default) and count constraint rows that do no work:

* rows whose lower or upper bound evaluates to +/- infinity (a limit param
  left at an infinite default that the rule did not skip);
* rows with a constant body (a rule that returned Constraint.Feasible, which
  Pyomo builds and writes to the LP as an empty row; only Constraint.Skip
  drops the index);
* rows whose finite bound is at least --big_bound in magnitude (a "large
  number as no limit" input sentinel).

Such rows add nothing to the problem but cost memory, LP size and solver
scaling. The first two kinds are removed by returning Constraint.Skip from
the rule when the limit is at its default; sentinels want an optional input
with an infinite default instead.

Only scenario directories with inputs at their root (a single subproblem and
stage) are built; others are listed as skipped. Nothing is solved or written
to the scenario directories. Usage::

    python -m tests.scan_unbounded_constraint_rows
        [--scenario_location examples] [--output rows.csv] [--big_bound 1e6]
        [--fail_on_unbounded]

With --fail_on_unbounded the exit status is nonzero if any row has an
infinite bound or a constant body, if any model failed to build, or if no
model was built at all (an empty examples directory would otherwise pass
silently). The parallel test runner (scripts/run_tests_parallel.py) runs the
scan in this mode after its test lanes have regenerated the examples, so the
check runs in CI; sentinel-sized bounds are reported but never fail it.
"""

import argparse
import csv
import logging
import math
import os
import sys
import time
import warnings
from collections import defaultdict

from pyomo.environ import Constraint, value

from gridpath import run_scenario


def parse_arguments(args):
    parser = argparse.ArgumentParser(description=__doc__.split("Usage::")[0])
    parser.add_argument(
        "--scenario_location",
        default=os.path.join(os.path.dirname(__file__), "..", "examples"),
        help="Directory holding the scenario directories to build.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write the per-constraint counts to this CSV (default: print only).",
    )
    parser.add_argument(
        "--big_bound",
        type=float,
        default=1e6,
        help="Report finite bounds at least this large in magnitude (default 1e6).",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Do not print per-scenario progress."
    )
    parser.add_argument(
        "--fail_on_unbounded",
        action="store_true",
        help="Exit with status 1 if any row has an infinite bound or a constant "
        "body, if any model failed to build, or if no model was built.",
    )
    return parser.parse_args(args)


def body_is_constant(constraint_data):
    """Whether the row has no variables (e.g. it came from Constraint.Feasible)."""
    body = constraint_data.body
    if body.__class__ in (int, float):
        return True
    return getattr(body, "is_constant", lambda: False)()


def scan_instance(instance, stats, scenario, big_bound):
    for con in instance.component_objects(Constraint, active=True):
        st = stats[con.name]
        for idx in con:
            cd = con[idx]
            st["rows"] += 1
            st["scenarios"].add(scenario)
            if body_is_constant(cd):
                st["constant_rows"] += 1
                st["flagged_scenarios"].add(scenario)
                continue
            infinite = False
            for bound in (cd.lower, cd.upper):
                if bound is None:
                    continue
                try:
                    v = value(bound)
                except (ValueError, TypeError):
                    continue
                if v is None or isinstance(v, bool):
                    continue
                if math.isinf(v):
                    infinite = True
                elif abs(v) >= big_bound:
                    st["big_rows"] += 1
                    st["max_abs_finite_bound"] = max(st["max_abs_finite_bound"], abs(v))
                    st["flagged_scenarios"].add(scenario)
            if infinite:
                st["infinite_rows"] += 1
                st["flagged_scenarios"].add(scenario)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed = parse_arguments(args)
    warnings.filterwarnings("ignore")
    logging.disable(logging.CRITICAL)

    build_args = argparse.Namespace(quiet=True, skip_duals=True, report_timing=False)
    stats = defaultdict(
        lambda: {
            "rows": 0,
            "infinite_rows": 0,
            "constant_rows": 0,
            "big_rows": 0,
            "max_abs_finite_bound": 0.0,
            "scenarios": set(),
            "flagged_scenarios": set(),
        }
    )
    skipped, failed, built = [], [], 0
    start = time.time()
    for scenario in sorted(os.listdir(parsed.scenario_location)):
        scenario_directory = os.path.join(parsed.scenario_location, scenario)
        if not os.path.isdir(os.path.join(scenario_directory, "inputs")):
            skipped.append(scenario)
            continue
        try:
            _, instance = run_scenario.create_problem(
                scenario_directory, "", "", "", "", "", False, build_args
            )
        except Exception as e:  # report and keep going
            failed.append((scenario, "{}: {}".format(type(e).__name__, e)))
            continue
        built += 1
        scan_instance(instance, stats, scenario, parsed.big_bound)
        if not parsed.quiet:
            print("{} ({:.0f}s)".format(scenario, time.time() - start), flush=True)

    columns = [
        "constraint",
        "rows",
        "infinite_rows",
        "constant_rows",
        "big_rows",
        "max_abs_finite_bound",
        "n_scenarios",
        "n_scenarios_flagged",
        "example_flagged_scenario",
    ]
    rows = sorted(
        (
            [
                name,
                st["rows"],
                st["infinite_rows"],
                st["constant_rows"],
                st["big_rows"],
                st["max_abs_finite_bound"],
                len(st["scenarios"]),
                len(st["flagged_scenarios"]),
                min(st["flagged_scenarios"]) if st["flagged_scenarios"] else "",
            ]
            for name, st in stats.items()
        ),
        key=lambda r: -(r[2] + r[3] + r[4]),
    )
    if parsed.output is not None:
        with open(parsed.output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

    totals = {
        c: sum(st[c] for st in stats.values())
        for c in ["rows", "infinite_rows", "constant_rows", "big_rows"]
    }
    print(
        "Built {} scenarios ({} skipped without root-level inputs, {} failed); "
        "{rows} constraint rows: {infinite_rows} with an infinite bound, "
        "{constant_rows} with a constant body, {big_rows} with a bound >= {big}".format(
            built, len(skipped), len(failed), big=parsed.big_bound, **totals
        )
    )
    for row in rows:
        if row[2] + row[3] + row[4] > 0:
            print(
                "  {}: {} infinite, {} constant, {} big of {} rows (e.g. {})".format(
                    row[0], row[2], row[3], row[4], row[1], row[8]
                )
            )
    for scenario, error in failed:
        print("  FAILED {}: {}".format(scenario, error))

    if parsed.fail_on_unbounded:
        problems = []
        if built == 0:
            problems.append("no scenario was built")
        if failed:
            problems.append("{} scenario(s) failed to build".format(len(failed)))
        if totals["infinite_rows"] or totals["constant_rows"]:
            problems.append(
                "{} row(s) with an infinite bound and {} with a constant body "
                "(return Constraint.Skip when a limit is at its default)".format(
                    totals["infinite_rows"], totals["constant_rows"]
                )
            )
        if problems:
            print("FAILED: " + "; ".join(problems))
            sys.exit(1)
    return totals


if __name__ == "__main__":
    main()
