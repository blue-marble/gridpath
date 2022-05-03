# Copyright 2016-2020 Blue Marble Analytics LLC.
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
This script iterates over all modules required for a GridPath scenario and
calls their *write_model_inputs()* method, which queries the GridPath
database and writes the .tab input files to the scenario directory.

The main() function of this script can also be called with the
*gridpath_get_inputs* command when GridPath is installed.
"""

from argparse import ArgumentParser
import csv
from multiprocessing import Pool
import os.path
import pandas as pd
import sys
import warnings

from db.common_functions import connect_to_database
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from gridpath.common_functions import (
    determine_scenario_directory,
    create_directory_if_not_exists,
    get_db_parser,
    get_required_e2e_arguments_parser,
    get_parallel_get_inputs_parser,
)
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.auxiliary.scenario_chars import (
    OptionalFeatures,
    SubScenarios,
    get_subproblem_structure_from_db,
    SolverOptions,
)


def write_model_inputs(
    scenario_directory,
    subproblem_structure,
    multi_stage,
    modules_to_use,
    scenario_id,
    subscenarios,
    db_path,
    n_parallel_subproblems,
):
    """
    For each module, load the inputs from the database and write out the inputs
    into .tab files, which will be used to construct the optimization problem.

    :param scenario_directory: local scenario directory
    :param subproblem_structure: SubProblems object with info on the
        subproblem/stage structure
    :param modules_to_use: list of imported modules (Python <class 'module'>
        objects)
    :param scenario_id: integer
    :param subscenarios: SubScenarios object with all subscenario info
    :param db_path: database connection
    :param n_parallel_subproblems: int; get inputs for subproblems in parallel


    :return:
    """
    # TODO: should probably delete the whole scenario directory first,
    #  as previous scenario with the same name could have had a different
    #  subproblem-stage structure
    # Delete auxiliary files that may have existed before to avoid phantom
    # files
    delete_prior_aux_files(scenario_directory=scenario_directory)

    # Determine whether we will have subproblem directories
    # We write the subproblem directories if we have multiple subproblems or if we
    # have a single subroblem with stages (the multi_stage flag will be True)
    if len(subproblem_structure.SUBPROBLEM_STAGES) == 1 and multi_stage is False:
        make_subproblem_directories = False
    else:
        make_subproblem_directories = True

    # Do a few checks on parallelization request
    if n_parallel_subproblems < 1:
        warnings.warn(
            "n_parallel_subproblem can't be 0. Solving without " "parallelization."
        )
        n_parallel_subproblems = 1

    if len(subproblem_structure.SUBPROBLEM_STAGES) == 1 and n_parallel_subproblems > 1:
        warnings.warn(
            "Only one subproblem in scenario. Parallelization " "not possible."
        )
        n_parallel_subproblems = 1

    # If no parallelization requested, loop through the subproblems
    if n_parallel_subproblems == 1:
        for subproblem in subproblem_structure.SUBPROBLEM_STAGES.keys():
            get_inputs_for_subproblem(
                scenario_directory=scenario_directory,
                subproblem_structure=subproblem_structure,
                subproblem=subproblem,
                make_subproblem_directories=make_subproblem_directories,
                modules_to_use=modules_to_use,
                scenario_id=scenario_id,
                subscenarios=subscenarios,
                db_path=db_path,
            )
    else:
        pool_data = tuple(
            [
                [
                    scenario_directory,
                    subproblem_structure,
                    subproblem,
                    make_subproblem_directories,
                    modules_to_use,
                    scenario_id,
                    subscenarios,
                    db_path,
                ]
                for subproblem in subproblem_structure.SUBPROBLEM_STAGES.keys()
            ]
        )

        pool = Pool(n_parallel_subproblems)
        pool.map(get_inputs_for_subproblem_pool, pool_data)
        pool.close()


def get_inputs_for_subproblem(
    scenario_directory,
    subproblem_structure,
    subproblem,
    make_subproblem_directories,
    modules_to_use,
    scenario_id,
    subscenarios,
    db_path,
):

    loaded_modules = load_modules(modules_to_use=modules_to_use)

    # First make inputs directory if needed
    # If there are subproblems/stages, input directory will be nested
    if make_subproblem_directories:
        subproblem_str = str(subproblem)
    else:
        subproblem_str = ""

    stages = subproblem_structure.SUBPROBLEM_STAGES[subproblem]
    if len(stages) == 1:
        make_stage_directories = False
    else:
        make_stage_directories = True

    for stage in stages:
        if make_stage_directories:
            stage_str = str(stage)
        else:
            stage_str = ""
        inputs_directory = os.path.join(
            scenario_directory, subproblem_str, stage_str, "inputs"
        )
        if not os.path.exists(inputs_directory):
            os.makedirs(inputs_directory)

        # Delete input files that may have existed before to avoid
        # phantom inputs
        delete_prior_inputs(inputs_directory=inputs_directory)

        # Write model input .tab files for each of the loaded_modules if
        # appropriate. Note that all input files are saved in the
        # input_directory, even the non-temporal inputs that are not
        # dependent on the subproblem or stage. This simplifies the file
        # structure at the expense of unnecessarily duplicating
        # non-temporal input files such as projects.tab.
        conn = connect_to_database(db_path=db_path)
        for m in loaded_modules:
            if hasattr(m, "write_model_inputs"):
                m.write_model_inputs(
                    scenario_directory=scenario_directory,
                    scenario_id=scenario_id,
                    subscenarios=subscenarios,
                    subproblem=subproblem_str,
                    stage=stage_str,
                    conn=conn,
                )
            else:
                pass
        conn.close()

    # If there are stages in the subproblem, we also need a pass-through
    # directory and to write headers of the pass-through input file
    # TODO: this should probably be moved to the module responsible for
    #  writing to this file
    # TODO: how to deal with pass-through inputs
    # TODO: we probably don't need a directory for the
    #  pass-through inputs, as it's only one file
    if len(stages) > 1:
        # Create the commitment pass-through file (also deletes any
        # prior results)
        # First create the pass-through directory if it doesn't
        # exist
        # TODO: need better handling of deleting prior results?
        pass_through_directory = os.path.join(
            scenario_directory, str(subproblem), "pass_through_inputs"
        )
        if not os.path.exists(pass_through_directory):
            os.makedirs(pass_through_directory)
        # Write the headers of the pass through files
        for m in loaded_modules:
            if hasattr(m, "write_pass_through_file_headers"):
                m.write_pass_through_file_headers(
                    pass_through_directory=pass_through_directory
                )
            else:
                pass


def get_inputs_for_subproblem_pool(pool_datum):
    """
    Helper function to easily pass to pool.map if running subproblems in
    parallel
    """
    [
        scenario_directory,
        subproblem_structure,
        subproblem,
        make_subproblem_directories,
        modules_to_use,
        scenario_id,
        subscenarios,
        db_path,
    ] = pool_datum

    get_inputs_for_subproblem(
        scenario_directory=scenario_directory,
        subproblem_structure=subproblem_structure,
        subproblem=subproblem,
        make_subproblem_directories=make_subproblem_directories,
        modules_to_use=modules_to_use,
        scenario_id=scenario_id,
        subscenarios=subscenarios,
        db_path=db_path,
    )


def delete_prior_aux_files(scenario_directory):
    """
    Delete all auxiliary files that may exist in the scenario directory
    :param scenario_directory: the scenario directory
    :return:
    """
    prior_aux_files = [
        "features.csv",
        "scenario_description.csv",
        "solver_options.csv",
        "linked_subproblems_map.csv",
    ]

    for f in prior_aux_files:
        if f in os.listdir(scenario_directory):
            os.remove(os.path.join(scenario_directory, f))
        else:
            pass


def delete_prior_inputs(inputs_directory):
    """
    Delete all .tab files that may exist in the specified directory
    :param inputs_directory: local directory where .tab files are saved
    :return:
    """
    prior_input_tab_files = [
        f for f in os.listdir(inputs_directory) if f.endswith(".tab")
    ]

    for f in prior_input_tab_files:
        os.remove(os.path.join(inputs_directory, f))


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(
        add_help=True,
        parents=[
            get_db_parser(),
            get_required_e2e_arguments_parser(),
            get_parallel_get_inputs_parser(),
        ],
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def write_features_csv(scenario_directory, feature_list):
    """
    Write the features.csv file that will be used to determine which
    GridPath modules to include
    :return:
    """
    with open(
        os.path.join(scenario_directory, "features.csv"), "w", newline=""
    ) as features_csv_file:
        writer = csv.writer(features_csv_file, delimiter=",", lineterminator="\n")

        # Write header
        writer.writerow(["features"])

        for feature in feature_list:
            writer.writerow([feature])


def write_scenario_description(
    scenario_directory, scenario_id, scenario_name, optional_features, subscenarios
):
    """

    :param scenario_directory:
    :param scenario_id:
    :param scenario_name:
    :param optional_features:
    :param subscenarios:
    :return:
    """
    feature_list = optional_features.get_all_available_features()
    subscenario_list = subscenarios.get_all_available_subscenarios()

    with open(
        os.path.join(scenario_directory, "scenario_description.csv"), "w", newline=""
    ) as scenario_description_file:
        writer = csv.writer(
            scenario_description_file, delimiter=",", lineterminator="\n"
        )

        # Scenario ID and scenario name
        writer.writerow(["scenario_id", scenario_id])
        writer.writerow(["scenario_name", scenario_name])

        # Optional features
        for feature in feature_list:
            writer.writerow(
                [
                    "of_{}".format(feature),
                    getattr(optional_features, "OF_{}".format(feature.upper())),
                ]
            )

        # Subscenarios
        for subscenario in subscenario_list:
            writer.writerow([subscenario, getattr(subscenarios, subscenario.upper())])


def write_units_csv(scenario_directory, conn):
    """

    :param scenario_directory:
    :param conn:
    :return:
    """
    sql = """
        SELECT metric, unit
        FROM mod_units;
        """
    df = pd.read_sql(sql, conn)
    df.to_csv(os.path.join(scenario_directory, "units.csv"), index=False)


def write_solver_options(scenario_directory, solver_options):
    """
    :param scenario_directory:
    :param solver_options:

    If a solver_options_id is specified, writer the solver options to the
    scenario directory.
    """
    if solver_options.SOLVER_NAME is None and solver_options.SOLVER_OPTIONS is None:
        pass
    else:
        with open(
            os.path.join(scenario_directory, "solver_options.csv"), "w", newline=""
        ) as solver_options_file:
            writer = csv.writer(solver_options_file, delimiter=",")
            writer.writerow(["solver_name", solver_options.SOLVER_NAME])
            for opt in solver_options.SOLVER_OPTIONS.keys():
                writer.writerow([opt, solver_options.SOLVER_OPTIONS[opt]])


def write_linked_subproblems_map(scenario_directory, conn, subscenarios):
    sql = """
        SELECT subproblem_id as subproblem, stage_id as stage, timepoint, 
        subproblem_id + 1 as subproblem_to_link, 
        linked_timepoint, number_of_hours_in_timepoint
        FROM inputs_temporal
        WHERE linked_timepoint IS NOT NULL
        AND temporal_scenario_id = ?;
        """

    df = pd.read_sql(sql=sql, con=conn, params=(subscenarios.TEMPORAL_SCENARIO_ID,))

    # Only write this file if there are any linked problems
    if not df.empty:
        df.to_csv(
            os.path.join(scenario_directory, "linked_subproblems_map.csv"), index=False
        )


def main(args=None):
    """

    :return:
    """
    # Retrieve DB location and scenario_id and/or name from args
    if args is None:
        args = sys.argv[1:]

    parsed_arguments = parse_arguments(args=args)

    db_path = parsed_arguments.database
    scenario_id_arg = parsed_arguments.scenario_id
    scenario_name_arg = parsed_arguments.scenario
    scenario_location = parsed_arguments.scenario_location

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    if not parsed_arguments.quiet:
        print("Getting inputs... (connected to database {})".format(db_path))

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg,
        scenario_name_arg=scenario_name_arg,
        c=c,
        script="get_scenario_inputs",
    )

    # Determine scenario directory and create it if needed
    scenario_directory = determine_scenario_directory(
        scenario_location=scenario_location, scenario_name=scenario_name
    )
    create_directory_if_not_exists(directory=scenario_directory)

    # Get scenario characteristics (features, scenario_id, subscenarios, subproblems)
    # TODO: it seems these fail silently if empty; we may want to implement
    #  some validation
    optional_features = OptionalFeatures(conn=conn, scenario_id=scenario_id)
    subscenarios = SubScenarios(conn=conn, scenario_id=scenario_id)
    subproblem_structure = get_subproblem_structure_from_db(
        conn=conn, scenario_id=scenario_id
    )
    solver_options = SolverOptions(conn=conn, scenario_id=scenario_id)

    # Determine requested features and use this to determine what modules to
    # load for Gridpath
    feature_list = optional_features.get_active_features()
    # If any subproblem's stage list is non-empty, we have stages, so set
    # the stages_flag to True to pass to determine_modules below
    # This tells the determine_modules function to include the
    # stages-related modules
    stages_flag = any(
        [
            len(subproblem_structure.SUBPROBLEM_STAGES[subp]) > 1
            for subp in list(subproblem_structure.SUBPROBLEM_STAGES.keys())
        ]
    )

    # Figure out which modules to use and load the modules
    modules_to_use = determine_modules(features=feature_list, multi_stage=stages_flag)

    # Get appropriate inputs from database and write the .tab file model inputs
    write_model_inputs(
        scenario_directory=scenario_directory,
        subproblem_structure=subproblem_structure,
        multi_stage=stages_flag,
        modules_to_use=modules_to_use,
        scenario_id=scenario_id,
        subscenarios=subscenarios,
        db_path=db_path,
        n_parallel_subproblems=int(parsed_arguments.n_parallel_get_inputs),
    )

    # Save the list of optional features to a file (will be used to determine
    # modules without database connection)
    write_features_csv(scenario_directory=scenario_directory, feature_list=feature_list)
    # Write full scenario description
    write_scenario_description(
        scenario_directory=scenario_directory,
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        optional_features=optional_features,
        subscenarios=subscenarios,
    )

    # Write the units used for all metrics
    write_units_csv(scenario_directory, conn)

    # Write the solver options file if needed
    write_solver_options(
        scenario_directory=scenario_directory, solver_options=solver_options
    )

    # Write the subproblem linked timepoints map file if needed
    write_linked_subproblems_map(scenario_directory, conn, subscenarios)

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    main()
