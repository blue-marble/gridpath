#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This script iterates over all modules required for a GridPath scenario and
calls their *write_model_inputs()* method, which queries the GridPath
database and writes the .tab input files to the scenario directory.

The main() function of this script can also be called with the
*gridpath_get_inputs* command when GridPath is installed.
"""

from __future__ import print_function

from builtins import str
from argparse import ArgumentParser
import csv
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from gridpath.common_functions import determine_scenario_directory, \
    create_directory_if_not_exists, get_db_parser, get_required_e2e_arguments_parser
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.auxiliary.scenario_chars import Scenario


def write_model_inputs(scenario_directory, scenario, loaded_modules):
    """
    For each module, load the inputs from the database and write out the inputs
    into .tab files, which will be used to construct the optimization problem.

    :param scenario_directory: local scenario directory
    :param scenario: Scenario object
    :param loaded_modules: list of imported modules (Python <class 'module'>
        objects)

    :return:
    """
    subproblems_list = scenario.SUBPROBLEMS

    for subproblem, stages in scenario.SUBPROBLEM_STAGE_DICT.ites():
        for stage in stages:
            # if there are subproblems/stages, input directory will be nested
            if len(subproblems_list) > 1 and len(stages) > 1:
                pass
            elif len(scenario.SUBPROBLEMS) > 1:
                stage = ""
            elif len(stages) > 1:
                subproblem = ""
            else:
                subproblem = ""
                stage = ""
            inputs_directory = os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs"
            )
            if not os.path.exists(inputs_directory):
                os.makedirs(inputs_directory)

            # Delete auxiliary and input files that may have existed before to
            # avoid phantom files/inputs
            delete_prior_aux_files(scenario_directory=scenario_directory)
            delete_prior_inputs(inputs_directory=inputs_directory)

            # Write model input .tab files for each of the loaded_modules if
            # appropriate. Note that all input files are saved in the
            # input_directory, even the non-temporal inputs that are not
            # dependent on the subproblem or stage. This simplifies the file
            # structure at the expense of unnecessarily duplicating
            # non-temporal input files such as projects.tab.
            for m in loaded_modules:
                if hasattr(m, "write_model_inputs"):
                    m.write_model_inputs(
                        scenario_directory=scenario_directory,
                        scenario=scenario,
                        subproblem=subproblem,
                        stage=stage
                    )
                else:
                    pass


def delete_prior_aux_files(scenario_directory):
    """
    Delete all auxiliary files that may exist in the scenario directory
    :param scenario_directory: the scenario directory
    :return:
    """
    prior_aux_files = [
        "features.csv", "scenario_description.csv", "solver_options.csv",
        "linked_subproblems_map.csv"
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
        f for f in os.listdir(inputs_directory) if f.endswith('.tab')
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
        parents=[get_db_parser(), get_required_e2e_arguments_parser()]
    )
    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def write_features_csv(scenario_directory, feature_list):
    """
    Write the features.csv file that will be used to determine which
    GridPath modules to include
    :return:
    """
    with open(os.path.join(scenario_directory, "features.csv"), "w", newline="") as \
            features_csv_file:
        writer = csv.writer(
            features_csv_file, delimiter=",", lineterminator="\n"
        )

        # Write header
        writer.writerow(["features"])

        for feature in feature_list:
            writer.writerow([feature])


def write_scenario_description(
        scenario_directory, scenario_id, scenario_name, scenario
):
    """

    :param scenario_directory:
    :param scenario_id:
    :param scenario_name:
    :param scenario:
    :return:
    """
    with open(os.path.join(scenario_directory, "scenario_description.csv"),
              "w", newline="") as \
            scenario_description_file:
        writer = csv.writer(scenario_description_file, delimiter=",",
                            lineterminator="\n")

        # Scenario ID and scenario name
        writer.writerow(["scenario_id", scenario_id])
        writer.writerow(["scenario_name", scenario_name])

        # Optional features
        for k, v in scenario.feature_dict.items():
            writer.writerow([k, v])

        # Subscenarios
        for k, v in scenario.subscenarios_ids.items():
            writer.writerow([k, v])


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


def write_solver_options(scenario_directory, scenario):
    """
    :param scenario_directory:
    :param scenario:

    If a solver_options_id is specified, writer the solver options to the
    scenario directory.
    """
    if scenario.SOLVER is None and scenario.SOLVER_OPTIONS is None:
        pass
    else:
        with open(os.path.join(scenario_directory, "solver_options.csv"),
                  "w", newline="") as solver_options_file:
            writer = csv.writer(solver_options_file, delimiter=",")
            writer.writerow(["solver", scenario.SOLVER])
            for opt in scenario.SOLVER_OPTIONS.keys():
                writer.writerow([opt, scenario.SOLVER_OPTIONS[opt]])


def write_linked_subproblems_map(scenario_directory, scenario):
    sql = """
        SELECT subproblem_id as subproblem, stage_id as stage, timepoint, 
        subproblem_id + 1 as subproblem_to_link, 
        linked_timepoint, number_of_hours_in_timepoint
        FROM inputs_temporal
        WHERE linked_timepoint IS NOT NULL
        AND temporal_scenario_id = ?;
        """

    df = pd.read_sql(
        sql=sql,
        con=scenario.conn,
        params=(scenario.subscenario_ids["TEMPORAL_SCENARIO_ID"], )
    )

    # Only write this file if there are any linked problems
    if not df.empty:
        df.to_csv(
            os.path.join(scenario_directory, "linked_subproblems_map.csv"),
            index=False
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

    if not parsed_arguments.quiet:
        print("Getting inputs... (connected to database {})".format(db_path))

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg,
        scenario_name_arg=scenario_name_arg,
        c=conn.cursor(),
        script="get_scenario_inputs"
    )

    # Determine scenario directory and create it if needed
    scenario_directory = determine_scenario_directory(
        scenario_location=scenario_location,
        scenario_name=scenario_name
    )
    create_directory_if_not_exists(directory=scenario_directory)

    # Get scenario characteristics (features, subscenarios, subproblems)
    # TODO: it seems these fail silently if empty; we may want to implement
    #  some validation
    scenario = Scenario(conn, scenario_id)

    # Determine requested features and use this to determine what modules to
    # load for Gridpath
    # If any subproblem's stage list is non-empty, we have stages, so set
    # the stages_flag to True to pass to determine_modules below
    # This tells the determine_modules function to include the
    # stages-related modules
    stages_flag = any([
        len(scenario.SUBPROBLEM_STAGE_DICT[subp]) > 1
        for subp in scenario.SUBPROBLEM_STAGE_DICT.keys()
    ])

    # Figure out which modules to use and load the modules
    modules_to_use = determine_modules(features=scenario.feature_list,
                                       multi_stage=stages_flag)
    loaded_modules = load_modules(modules_to_use=modules_to_use)

    # Get appropriate inputs from database and write the .tab file model inputs
    write_model_inputs(
        scenario_directory=scenario_directory,
        scenario=scenario,
        loaded_modules=loaded_modules
    )

    # Save the list of optional features to a file (will be used to determine
    # modules without database connection)
    write_features_csv(
        scenario_directory=scenario_directory,
        feature_list=scenario.feature_list
    )
    # Write full scenario description
    write_scenario_description(
        scenario_directory=scenario_directory,
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        scenario=scenario
    )

    # Write the units used for all metrics
    write_units_csv(scenario_directory, conn)

    # Write the solver options file if needed
    write_solver_options(
        scenario_directory=scenario_directory,
        scenario=scenario
    )

    # Write the subproblem linked timepoints map file if needed
    write_linked_subproblems_map(
        scenario_directory=scenario_directory,
        scenario=scenario
    )

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    main()
