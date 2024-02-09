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
Does not cover all possible cases yet.
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
    parser.add_argument("-csv", "--csv_path")

    parser.add_argument("-out_dir", "--output_directory")

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def create_temporal_scenario_iterations_csv(n_passes, filepath, output_directory):
    with open(os.path.join(output_directory, "iterations.csv"), "w") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(
            ["weather_iteration", "hydro_iteration", "availability_iteration"]
        )

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
    random.seed(0)
    i = random.randrange(len(starting_list))
    starting_list[i], starting_list[-1] = starting_list[-1], starting_list[i]
    iteration = starting_list.pop()

    return iteration


def random_keep(starting_list):
    random.seed(0)
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

    create_temporal_scenario_iterations_csv(
        n_passes=int(parsed_args.n_passes),
        filepath=parsed_args.csv_path,
        output_directory=parsed_args.output_directory,
    )
    sort_final_file(
        filepath=os.path.join(parsed_args.output_directory, "iterations.csv")
    )


if __name__ == "__main__":
    main()
