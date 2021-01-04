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
calls their *import_results_into_database()* method, which loads the
scenario results files into their respective database table.

The main()_ function of this script can also be called with the
*gridpath_import_results* command when GridPath is installed.
"""

from argparse import ArgumentParser
import os.path
import pandas as pd
import sys

from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from gridpath.common_functions import determine_scenario_directory, \
    get_db_parser, get_required_e2e_arguments_parser
from db.common_functions import connect_to_database, spin_on_database_lock
from db.utilities.scenario import delete_scenario_results
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.auxiliary.scenario_chars import ScenarioSubproblemStructureDB


def import_results_into_database(
    loaded_modules, scenario_id, subproblem_structure, cursor, db,
    scenario_directory, quiet, subproblems_to_process
):
    """

    :param loaded_modules:
    :param scenario_id:
    :param subproblem_structure:
    :param cursor:
    :param db:
    :param scenario_directory:
    :param quiet: boolean
    :return:
    """

    subproblems_list = subproblem_structure.ALL_SUBPROBLEMS
    for subproblem in subproblems_to_process:
        stages = subproblem_structure.STAGES_BY_SUBPROBLEM[subproblem]
        for stage in stages:
            # if there are subproblems/stages, input directory will be nested
            if len(subproblems_list) > 1 and len(stages) > 1:
                results_directory = os.path.join(scenario_directory,
                                                 str(subproblem),
                                                 str(stage),
                                                 "results")
                if not quiet:
                    print("--- subproblem {}".format(str(subproblem)))
                    print("--- stage {}".format(str(stage)))
            elif len(subproblem_structure.ALL_SUBPROBLEMS) > 1:
                results_directory = os.path.join(scenario_directory,
                                                 str(subproblem),
                                                 "results")
                if not quiet:
                    print("--- subproblem {}".format(str(subproblem)))
            elif len(stages) > 1:
                results_directory = os.path.join(scenario_directory,
                                                 str(stage),
                                                 "results")
                if not quiet:
                    print("--- stage {}".format(str(stage)))
            else:
                results_directory = os.path.join(scenario_directory,
                                                 "results")

            # Import results_scenario data
            c = db.cursor()
            with open(os.path.join(results_directory,
                                   "termination_condition.txt"),
                      "r") as f:
                termination_condition = f.read()

            termination_condition_sql = """
                INSERT INTO results_scenario
                (scenario_id, subproblem_id, stage_id, 
                solver_termination_condition)
                VALUES (?, ?, ?, ?)
            ;"""
            termination_condition_data = \
                (scenario_id, subproblem, stage, termination_condition)
            spin_on_database_lock(
                conn=db, cursor=c, sql=termination_condition_sql,
                data=termination_condition_data, many=False
            )

            with open(os.path.join(results_directory, "solver_status.txt"),
                      "r") as status_f:
                solver_status = status_f.read()

            # Only import other results if solver status was "ok"
            # When the problem is infeasible, the solver status is "warning"
            # If there's no solution, variables remain uninitialized,
            # throwing an error at some point during results-export,
            # so we don't attempt to import missing results into the database
            if solver_status == "ok":
                # Import the objective function value
                with open(os.path.join(results_directory,
                                       "objective_function_value.txt"),
                          "r") as f:
                    objective_function = f.read()

                obj_sql = """
                    UPDATE results_scenario
                    SET objective_function_value = ?
                    WHERE scenario_id = ?
                    AND subproblem_id = ?
                    AND stage_id = ?
                ;"""

                obj_data = \
                    (objective_function, scenario_id, subproblem,  stage)
                spin_on_database_lock(
                    conn=db, cursor=c, sql=obj_sql,
                    data=obj_data, many=False
                )

                for m in loaded_modules:
                    if hasattr(m, "import_results_into_database"):
                        m.import_results_into_database(
                            scenario_id=scenario_id,
                            subproblem=subproblem,
                            stage=stage,
                            c=cursor,
                            db=db,
                            results_directory=results_directory,
                            quiet=quiet
                        )
                    else:
                        pass
            else:
                if not quiet:
                    print("""
                    Solver status for subproblem {}, stage {} was '{}', 
                    not 'ok', so there are no results to import. 
                    Termination condition was '{}'.
                    """.format(subproblem, stage, solver_status,
                               termination_condition)
                          )


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    :param args: 
    :return: 
    """
    parser = ArgumentParser(
        add_help=True,
        parents=[get_db_parser(), get_required_e2e_arguments_parser()]
    )
    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def main(subproblems_to_process=None, args=None):
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
    quiet = parsed_arguments.quiet

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    if not parsed_arguments.quiet:
        print("Importing results... (connected to database {})".format(db_path))

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg, scenario_name_arg=scenario_name_arg,
        c=c, script="import_scenario_results")

    subproblems = ScenarioSubproblemStructureDB(conn=conn, scenario_id=scenario_id)

    # Determine scenario directory
    scenario_directory = determine_scenario_directory(
        scenario_location=scenario_location,
        scenario_name=scenario_name
    )

    # Check that the saved scenario_id matches
    sc_df = pd.read_csv(
        os.path.join(scenario_directory, "scenario_description.csv"),
        header=None, index_col=0
    )
    scenario_id_saved = int(sc_df.loc["scenario_id", 1])
    if scenario_id_saved != scenario_id:
        raise AssertionError("ERROR: saved scenario_id does not match")

    # Delete all previous results for this scenario_id
    # Each module also makes sure results are deleted, but this step ensures
    # that if a scenario_id was run with different modules before, we also
    # delete previously imported "phantom" results
    delete_scenario_results(conn=conn, scenario_id=scenario_id)

    # Go through modules
    modules_to_use = determine_modules(scenario_directory=scenario_directory)
    loaded_modules = load_modules(modules_to_use)

    # Import appropriate results into database
    import_results_into_database(
        loaded_modules=loaded_modules,
        scenario_id=scenario_id,
        subproblem_structure=subproblems,
        cursor=c,
        db=conn,
        scenario_directory=scenario_directory,
        quiet=quiet,
        subproblems_to_process=subproblems_to_process
    )

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    main()
