# Copyright 2016-2024 Blue Marble Analytics LLC.
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
Create Temporal Iterations CSV
******************************

Create temporal iterations CSV from user-defined params. Does not cover all
possible cases yet.

===================
What this step does
===================

This module builds the temporal ``iterations.csv`` that tells GridPath which
combinations of weather, hydro, and availability iterations to run. It reads
the user-defined ``--iterations_csv_path`` (which specifies, per dimension, the
sampling "mode" and the iterations to draw from) and writes an
``iterations.csv`` -- with ``weather_iteration``, ``hydro_iteration``, and
``availability_iteration`` columns -- into ``--output_directory``. This file
ties together the per-dimension Monte Carlo draws produced by the earlier steps
(e.g., ``create_monte_carlo_weather_draws``) into the actual set of scenario
iterations the model runs.

===========
Methodology
===========

The input file at ``--iterations_csv_path`` is a CSV with one column per
dimension: ``weather``, ``hydro``, and ``availability``. Within each column the
*first* data row holds that dimension's sampling **mode** (a string), and the
remaining non-empty rows list the iteration numbers available to draw from for
that dimension. The columns may be of unequal length; trailing blank cells are
ignored.

----------------
Sampling modes
----------------

The mode in each column's first row controls how iterations are selected for
that dimension:

    * ``loop`` -- iterate over every listed iteration in order. This is the
      driving mode: only the ``weather`` (and, when also ``loop``, the
      ``hydro``) dimension uses it to enumerate combinations.
    * ``ordered`` -- step through the listed iterations sequentially, advancing
      an index by one each time a value is requested.
    * ``random_keep`` -- draw an iteration uniformly at random, leaving the pool
      unchanged (sampling with replacement).
    * ``random_remove`` -- draw an iteration uniformly at random and remove it
      from the pool (sampling without replacement).
    * ``all`` -- always return the first listed iteration.

------------------------------
How combinations are generated
------------------------------

The current implementation only enumerates combinations when the ``weather``
mode is ``loop``; if ``weather`` uses any other mode, no rows are written.
Given ``weather`` is ``loop``:

    * If ``hydro`` is also ``loop``, the script writes one row for every
      ``(weather_iteration, hydro_iteration)`` pair (a full nested loop), with
      the ``availability_iteration`` for each row chosen according to the
      ``availability`` mode.
    * Otherwise, for each ``weather_iteration`` a single ``hydro_iteration`` is
      chosen according to the ``hydro`` mode and a single
      ``availability_iteration`` is chosen according to the ``availability``
      mode, producing one row per weather iteration.

The ``--n_passes`` argument (default ``1``) repeats this whole generation
process ``n_passes`` times, with each pass starting from a fresh copy of the
iteration pools; this is useful with the random modes to accumulate additional
draws. After all passes complete, ``iterations.csv`` is sorted ascending by
``weather_iteration``, then ``hydro_iteration``, then ``availability_iteration``.

------------------------
Reproducibility (seeding)
------------------------

The random sampling modes (``random_keep`` and ``random_remove``) draw from
Python's ``random`` module. By default ``--seed`` is unset, so the module is
seeded from system entropy and repeated runs produce different draws. Pass
``--seed <int>`` to seed the RNG once, up front, before any pass begins;
re-running with the same seed (and the same inputs and ``--n_passes``) then
reproduces the identical ``iterations.csv``. The non-random modes (``loop``,
``ordered``, ``all``) are deterministic regardless of the seed.

=====
Usage
=====

>>> python -m data_toolkit.temporal.create_temporal_iteration_csv --iterations_csv_path PATH/TO/ITERATIONS/CSV --output_directory PATH/TO/OUTPUT/DIR

===================
Input prerequisites
===================

This module requires a user-defined iterations CSV at ``--iterations_csv_path``
with the columns ``weather``, ``hydro``, and ``availability`` populated as
described above (a mode in the first row, followed by the iteration numbers to
draw from).

=========
Settings
=========
    * n_passes
    * iterations_csv_path
    * output_directory
    * seed
"""

import sys
from argparse import ArgumentParser
import csv
import os.path
import pandas as pd
import random

N_PASSES_DEFAULT = 1


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """

    parser = ArgumentParser(add_help=True)

    parser.add_argument(
        "-n",
        "--n_passes",
        default=N_PASSES_DEFAULT,
        help=f"Defaults to {N_PASSES_DEFAULT}.",
    )
    parser.add_argument("-csv", "--iterations_csv_path")

    parser.add_argument("-o", "--output_directory")

    parser.add_argument(
        "-s",
        "--seed",
        default=None,
        help="Random seed for the random sampling modes (random_keep, "
        "random_remove). Defaults to None (no seeding; draws differ each run). "
        "Set an integer for reproducible draws.",
    )

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def create_temporal_scenario_iterations_csv(
    n_passes, filepath, output_directory, seed=None
):
    # Seed the RNG once, up front, before any pass begins, so that the random
    # sampling modes (random_keep / random_remove) are reproducible when a seed
    # is provided. seed=None falls back to system (non-reproducible)
    random.seed(seed)

    with open(os.path.join(output_directory, "iterations.csv"), "w") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(
            ["weather_iteration", "hydro_iteration", "availability_iteration"]
        )

    # print(os.path.abspath(filepath))
    df = pd.read_csv(filepath)

    weather_df = df["weather"]
    weather_list = [i[1] for i in weather_df.items()]
    weather_mode = weather_list[0]
    weather_iterations_pass = [i for i in weather_list[1:] if not pd.isna(i)]

    hydro_df = df["hydro"]
    hydro_list = [i[1] for i in hydro_df.items()]
    hydro_mode = hydro_list[0]
    hydro_iterations_pass = [i for i in hydro_list[1:] if not pd.isna(i)]

    availability_df = df["availability"]
    availability_list = [i[1] for i in availability_df.items()]
    availability_mode = availability_list[0]
    availability_iterations_pass = [i for i in availability_list[1:] if not pd.isna(i)]

    # TODO: possibly remove
    weather_iteration, hydro_iteration, availability_iteration = None, None, None

    for n in range(n_passes):
        weather_iterations = weather_iterations_pass.copy()
        hydro_iterations = hydro_iterations_pass.copy()
        availability_iterations = availability_iterations_pass.copy()

        av_current_index = 0
        hy_current_index = 0
        if weather_mode == "loop":
            for weather_iteration in weather_iterations:
                if hydro_mode == "loop":
                    for hydro_iteration in hydro_iterations:
                        (
                            availability_iteration,
                            av_current_index,
                        ) = get_availability_iteration(
                            availability_mode=availability_mode,
                            availability_iterations=availability_iterations,
                            av_current_index=av_current_index,
                        )

                        with open(
                            os.path.join(output_directory, "iterations.csv"), "a"
                        ) as f_out:
                            writer = csv.writer(f_out, delimiter=",")
                            writer.writerow(
                                [
                                    weather_iteration,
                                    hydro_iteration,
                                    availability_iteration,
                                ]
                            )
                else:
                    if hydro_mode == "ordered":
                        hydro_iteration = hydro_iterations[hy_current_index]
                        hy_current_index += 1
                    elif hydro_mode == "random_remove":
                        hydro_iteration = random_remove(hydro_iterations)
                    elif hydro_mode == "all":
                        hydro_iteration = hydro_iterations[0]
                    elif hydro_mode == "random_keep":
                        hydro_iteration = random_keep(hydro_iterations)
                    else:
                        print("Unknown hydro mode")
                    (
                        availability_iteration,
                        av_current_index,
                    ) = get_availability_iteration(
                        availability_mode=availability_mode,
                        availability_iterations=availability_iterations,
                        av_current_index=av_current_index,
                    )

                    with open(
                        os.path.join(output_directory, "iterations.csv"), "a"
                    ) as f_out:
                        writer = csv.writer(f_out, delimiter=",")
                        writer.writerow(
                            [weather_iteration, hydro_iteration, availability_iteration]
                        )


def random_remove(starting_list):
    i = random.randrange(len(starting_list))
    starting_list[i], starting_list[-1] = starting_list[-1], starting_list[i]
    iteration = starting_list.pop()

    return iteration


def random_keep(starting_list):
    i = random.randrange(len(starting_list))
    iteration = starting_list[i]

    return iteration


def sort_final_file(filepath):
    df = pd.read_csv(filepath, delimiter=",")

    df = df.sort_values(
        ["weather_iteration", "hydro_iteration", "availability_iteration"],
        ascending=[True, True, True],
    )

    df.to_csv(filepath, index=False)


def get_availability_iteration(
    availability_mode, availability_iterations, av_current_index
):
    availability_iteration = None
    if availability_mode == "ordered":
        availability_iteration = availability_iterations[av_current_index]
        av_current_index += 1
    elif availability_mode == "random_remove":
        availability_iteration = random_remove(availability_iterations)
    elif availability_mode == "random_keep":
        availability_iteration = random_keep(availability_iterations)
    elif availability_mode == "all":
        availability_iteration = availability_iterations[0]
    else:
        print("Unknown availability mode.")

    return availability_iteration, av_current_index


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    os.makedirs(parsed_args.output_directory, exist_ok=True)

    create_temporal_scenario_iterations_csv(
        n_passes=int(parsed_args.n_passes),
        filepath=parsed_args.iterations_csv_path,
        output_directory=parsed_args.output_directory,
        seed=int(parsed_args.seed) if parsed_args.seed is not None else None,
    )
    sort_final_file(
        filepath=os.path.join(parsed_args.output_directory, "iterations.csv")
    )


if __name__ == "__main__":
    main()
