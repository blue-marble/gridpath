# Copyright 2016-2023 Blue Marble Analytics LLC.
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
Parallel gridpath_run: solve several scenarios at once, each in its own
process, from input files that have already been written. Results are not
imported into the database; to run the whole pipeline for several scenarios
at once use gridpath_run_e2e_parallel (:mod:`gridpath.run_end_to_end_parallel`),
which solves scenarios in parallel and imports their results one at a time.

The scenarios and their run_scenario options come from a CSV; see
:func:`read_scenarios_csv` for the format.
"""

from argparse import ArgumentParser
import csv
from multiprocessing import get_context
import sys

from gridpath.common_functions import get_version_parser
from gridpath.run_scenario import main as run_scenario_main


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True, parents=[get_version_parser()])

    # Scenario name and location options
    parser.add_argument(
        "--scenarios_csv",
        default="./scenarios_to_run.csv",
        help="The file containing the scenarios to run along with their "
        "run_scenario options.",
    )
    parser.add_argument(
        "--n_parallel_scenarios",
        type=int,
        required=True,
        help="Solve n scenarios in parallel.",
    )
    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


def read_scenarios_csv(scenarios_csv_path):
    """
    :param scenarios_csv_path: path to the scenarios CSV
    :return: list of (scenario_name, argument_list) tuples in the CSV's
        column order

    The CSV's top row is 'scenario' followed by the scenario names, one per
    column; each following row is an option name (without the leading
    dashes) followed by its value for each scenario. An empty cell passes
    the option as a bare flag, e.g. a 'log' row with empty cells turns on
    logging for every scenario::

        scenario,base,high_load
        scenario_location,/path/to/scenarios,/path/to/scenarios
        log,,

    The file is read with the utf-8-sig encoding, so a byte-order mark
    written by Excel (the likely way to produce the file) is dropped.
    """
    with open(scenarios_csv_path, "r", encoding="utf-8-sig") as scenarios_csv_in:
        reader = csv.reader(scenarios_csv_in, delimiter=",")
        header = next(reader)
        if not header or header[0] != "scenario":
            raise ValueError(
                "Scenarios must be in the top row with 'scenario' in the first "
                "column."
            )
        scenario_names = header[1:]
        args_by_scenario = [[] for _ in scenario_names]

        for row in reader:
            # Skip blank lines
            if not row or not row[0]:
                continue
            option = row[0]
            values = row[1:]
            if len(values) != len(scenario_names):
                raise ValueError(
                    f"Row '{option}' of {scenarios_csv_path} has {len(values)} "
                    f"value(s) for {len(scenario_names)} scenario(s)."
                )
            for scenario_args, value in zip(args_by_scenario, values):
                scenario_args.append(f"--{option}")
                if value != "":
                    scenario_args.append(value)

    return list(zip(scenario_names, args_by_scenario))


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    # Parse arguments
    parsed_args = parse_arguments(args)

    args_for_run_scenario = [
        ["--scenario", scenario_name] + scenario_args
        for scenario_name, scenario_args in read_scenarios_csv(
            parsed_args.scenarios_csv
        )
    ]

    # Create pool
    pool = get_context("spawn").Pool(parsed_args.n_parallel_scenarios)

    pool_data = tuple(args_for_run_scenario)
    pool.map(run_scenario_pool, pool_data)
    pool.close()
    pool.join()


def run_scenario_pool(pool_datum):
    """
    Helper function to pass to pool.map if solving scenarios in parallel.
    """
    run_scenario_main(
        args=pool_datum,
    )


if __name__ == "__main__":
    main()
