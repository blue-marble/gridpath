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
#
# simulate_unit_outages() function
# Copyright 2023 Moment Energy Insights LLC. Licensed under the Apache
# License, Version 2.0.
# Modifications Copyright 2024 Blue Marble Analytics LLC. Licensed under the
# Apache License, Version 2.0.

"""

"""
from argparse import ArgumentParser
import csv
from multiprocessing import get_context
import numpy as np
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-db", "--database", default="../../io.db")
    parser.add_argument("-stage", "--stage_id", default=1, help="Defaults to 1.")
    parser.add_argument("-n_iter", "--n_iterations")
    parser.add_argument(
        "-id", "--project_availability_scenario_id", default=1, help="Defaults to 1."
    )
    parser.add_argument(
        "-name",
        "--project_availability_scenario_name",
        default="ra_toolkit",
        help="Defaults to ra_toolkit.",
    )
    parser.add_argument("-out_dir", "--output_directory")
    parser.add_argument(
        "-o",
        "--overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing files.",
    )

    parser.add_argument(
        "-parallel",
        "--n_parallel_projects",
        default=1,
        help="The number of projects to simulate in parallel. Defaults to 1.",
    )

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_temporal_structure():
    stage_tmp_dict = {1: [tmp for tmp in range(1, 8760 + 1)]}

    return stage_tmp_dict


def get_weighted_availability_adjustment(project_df, tmps, seed):
    project_outage_adjustment = []
    project_hyb_stor_outage_adjustment = []

    for index, row in project_df.iterrows():
        unit = row["unit"]
        project = row["project"]
        n_units = row["n_units"]
        unit_weight = row["unit_weight"]
        outage_model = row["unit_fo_model"]
        unit_for = row["unit_for"]
        unit_mttr = row["unit_mttr"]
        hybrid_stor = row["hybrid_stor"]

        unit_for_array = np.full((len(tmps), 1), unit_for, dtype=float)

        unit_outage_adjustment = simulate_unit_outages(
            outage_model=outage_model,
            for_array=unit_for_array,
            mttr=unit_mttr,
            n_units=n_units,
            seed=seed,
        )

        if not hybrid_stor:
            project_outage_adjustment.append(unit_outage_adjustment * unit_weight)
        else:
            project_hyb_stor_outage_adjustment.append(
                unit_outage_adjustment * unit_weight
            )
    # Only sum the unit outages if there were units, otherwise, pass None
    if project_outage_adjustment:
        adjustment = sum(project_outage_adjustment)
    else:
        adjustment = None
    hyb_stor_adjustment = sum(project_hyb_stor_outage_adjustment)

    return adjustment, hyb_stor_adjustment


def simulate_project_availability(
    project_df,
    project,
    seed,
    n_iterations,
    stage_id,
    project_availability_scenario_id,
    project_availability_scenario_name,
    output_directory,
    overwrite,
):
    header = [
        "availability_iteration",
        "stage_id",
        "timepoint",
        "availability_derate_independent",
        "hyb_stor_cap_availability_derate_independent",
    ]

    filepath = os.path.join(
        output_directory,
        f"{project}-{project_availability_scenario_id}-{project_availability_scenario_name}.csv",
    )

    if not os.path.exists(filepath) or overwrite:
        with open(filepath, "w", newline="") as f:
            csvwriter = csv.writer(f)
            csvwriter.writerow(header)

    stage_tmp_dict = get_temporal_structure()

    # No stage simulation at this point; assume single stage
    tmps = stage_tmp_dict[1]

    for iter in range(1, n_iterations + 1):
        availability_derate, hyb_stor_derate = get_weighted_availability_adjustment(
            project_df=project_df, tmps=tmps, seed=seed
        )

        export_df = pd.DataFrame(
            {
                "availability_iteration": [iter] * len(tmps),
                "stage_id": [stage_id] * len(tmps),
                "timepoint": tmps,
                "availability_derate_independent": availability_derate,
                "hyb_stor_cap_availability_derate": hyb_stor_derate,
            }
        )

        export_df.to_csv(
            filepath,
            mode="a",
            header=False,
            index=False,
        )


def simulate_unit_outages(
    outage_model,
    for_array,
    mttr,
    n_units,
    seed,
    dt=1,
    starting_outage_states=None,
):
    """
    outage_model: ["Derate", "MC_independent", "MC_sequential"]
    FOR: numpy array with the length of the simulation window and the FOR as
        value; note this can vary by timepoint
    N_units: integer, number of units modeled
    starting_outage_states: array with the starting outage state (1/0) for
        each of the N units
    dt: outage timestep length
    """
    # Seed the simulation
    np.random.seed(seed)

    if starting_outage_states is None:
        starting_outage_states = []

    if outage_model == "Derate":
        availability = 1 - np.outer(for_array, np.ones(n_units))

    elif outage_model == "MC_independent":
        # randomly draw whether each unit is out using a uniform distribution
        # LHS is an array of the simulation window length with a random number
        # the RHS is an array of the simulation window length with the forced
        # outage rate
        # the results is an array with True/False (will be True FOR percent
        # of the time), so the final result (1.0 - ()) will be an array with
        # ones and zeros in which we'll have zeros FOR percent of the time
        availability = 1.0 - (
            np.random.rand(len(for_array), n_units)
            < np.outer(for_array, np.ones(n_units))
        )

    elif outage_model == "MC_sequential":
        # initialize with starting outage states, if they are provided.
        # Otherwise, initialize with randomly selected outages
        if np.size(starting_outage_states) == 0:
            avail_last = 1.0 - (
                np.random.rand(1, n_units) < np.outer(for_array[0], np.ones(n_units))
            )
        else:
            avail_last = starting_outage_states

        # calculate mean time to failure [MTTR = FOR * (MTTR + MTTF)]
        MTTF = float(mttr) * (1 / for_array - 1)

        # Randomly draw whether each unit fails or is repaired in each time
        # step using an exponential model
        availability = np.zeros([len(for_array), n_units])

        for t in range(len(for_array)):
            # If the unit was available in the last timepoint, use the MTTF
            # to determine if it will be available in the current timepoint
            # This depends on the timepoint-dependent FOR, so MTTF is indexed
            # by timepoint
            if_avail_last = (avail_last == 1) * (
                1.0 - (np.random.exponential(MTTF[t], n_units) < dt)
            )
            if_unavail_last = (avail_last == 0) * (
                np.random.exponential(float(mttr), n_units) < dt
            )
            avail_tmp = if_avail_last + if_unavail_last
            availability[t, :] = avail_tmp
            avail_last = avail_tmp

    else:
        availability = np.ones([len(for_array), n_units])

    outage_adjustment = np.mean(availability, axis=1)

    return outage_adjustment


def simulate_project_availability_pool(pool_datum):
    """
    Helper function to easily pass to pool.map if solving subproblems in
    parallel
    """
    [
        project_df,
        project,
        seed,
        n_iterations,
        stage_id,
        project_availability_scenario_id,
        project_availability_scenario_name,
        output_directory,
        overwrite,
    ] = pool_datum

    simulate_project_availability(
        project_df=project_df,
        project=project,
        seed=seed,
        n_iterations=n_iterations,
        stage_id=stage_id,
        project_availability_scenario_id=project_availability_scenario_id,
        project_availability_scenario_name=project_availability_scenario_name,
        output_directory=output_directory,
        overwrite=overwrite,
    )


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating availability iteration CSVs...")

    db = connect_to_database(parsed_args.database)

    projects = [
        i[0]
        for i in db.execute(
            """
        SELECT DISTINCT project FROM raw_data_unit_availability_params;
        """
        ).fetchall()
    ]

    pool_data = []
    seed = 0
    for project in projects:
        project_df = pd.read_sql(
            f"""
                SELECT * FROM raw_data_unit_availability_params
                WHERE project = '{project}'
                ;""",
            db,
        )

        pool_data.append(
            [
                project_df,
                project,
                seed,
                int(parsed_args.n_iterations),
                parsed_args.stage_id,
                parsed_args.project_availability_scenario_id,
                parsed_args.project_availability_scenario_name,
                parsed_args.output_directory,
                parsed_args.overwrite,
            ]
        )

        seed += 1

    pool_data = tuple(pool_data)

    # Pool must use spawn to work properly on Linux
    pool = get_context("spawn").Pool(int(parsed_args.n_parallel_projects))

    pool.map(simulate_project_availability_pool, pool_data)
    pool.close()


if __name__ == "__main__":
    main()
