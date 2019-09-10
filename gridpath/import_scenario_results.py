#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from argparse import ArgumentParser
import os.path
import sys

from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from gridpath.common_functions import determine_scenario_directory
from db.common_functions import connect_to_database
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.auxiliary.scenario_chars import SubProblems


def import_results_into_database(loaded_modules, scenario_id, subproblems,
                                 cursor, db, scenario_directory):
    """

    :param loaded_modules:
    :param scenario_id:
    :param subproblems:
    :param cursor:
    :param db:
    :param scenario_directory:
    :return:
    """

    subproblems_list = subproblems.SUBPROBLEMS
    for subproblem in subproblems_list:
        stages = subproblems.SUBPROBLEM_STAGE_DICT[subproblem]
        for stage in stages:
            # if there are subproblems/stages, input directory will be nested
            if len(subproblems_list) > 1 and len(stages) > 1:
                results_directory = os.path.join(scenario_directory,
                                                 str(subproblem),
                                                 str(stage),
                                                 "results")
                print("--- subproblem {}".format(str(subproblem)))
                print("--- stage {}".format(str(stage)))
            elif len(subproblems.SUBPROBLEMS) > 1:
                results_directory = os.path.join(scenario_directory,
                                                 str(subproblem),
                                                 "results")
                print("--- subproblem {}".format(str(subproblem)))
            elif len(stages) > 1:
                results_directory = os.path.join(scenario_directory,
                                                 str(stage),
                                                 "results")
                print("--- stage {}".format(str(stage)))
            else:
                results_directory = os.path.join(scenario_directory,
                                                 "results")
            if not os.path.exists(results_directory):
                os.makedirs(results_directory)

            for m in loaded_modules:
                if hasattr(m, "import_results_into_database"):
                    m.import_results_into_database(
                        scenario_id=scenario_id,
                        subproblem=subproblem,
                        stage=stage,
                        c=cursor,
                        db=db,
                        results_directory=results_directory
                    )
                else:
                    pass


def parse_arguments(args):
    """
    Parse arguments
    :param args: 
    :return: 
    """
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--database", help="The database file path.")
    parser.add_argument("--scenario",
                        help="The name of the scenario. Not needed if "
                             "scenario_id is specified.")
    parser.add_argument("--scenario_id",
                        help="The scenario_id from the database. Not needed "
                             "if scenario_name is specified.")
    parser.add_argument("--scenario_location",
                        help="The path to the base directory where the "
                             "scenario directory is located. Defaults to "
                             "'../scenarios' if not specified.")
    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def main(args=None):
    """

    :return:
    """
    if args is None:
        args = sys.argv[1:]

    parsed_arguments = parse_arguments(args=args)

    db_path = parsed_arguments.database
    scenario_id_arg = parsed_arguments.scenario_id
    scenario_name_arg = parsed_arguments.scenario
    scenario_location = parsed_arguments.scenario_location

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    print("Importing results... (connected to database {})".format(db_path))

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg, scenario_name_arg=scenario_name_arg,
        c=c, script="import_scenario_results")

    subproblems = SubProblems(cursor=c, scenario_id=scenario_id)

    # Determine scenario directory
    scenario_directory = determine_scenario_directory(
        scenario_location=scenario_location,
        scenario_name=scenario_name
    )

    # Check that the saved scenario_id matches
    with open(os.path.join(scenario_directory, "scenario_id.txt")) as \
            scenario_id_file:
        scenario_id_saved = int(scenario_id_file.read())
        if scenario_id_saved != scenario_id:
            raise AssertionError("ERROR: saved scenario_id does not match")

    # Go through modules
    modules_to_use = determine_modules(scenario_directory=scenario_directory)
    loaded_modules = load_modules(modules_to_use)

    # Import appropriate results into database
    import_results_into_database(
        loaded_modules=loaded_modules,
        scenario_id=scenario_id,
        subproblems=subproblems,
        cursor=c,
        db=conn,
        scenario_directory=scenario_directory
    )


if __name__ == "__main__":
    main()
