#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This script calls the __main__ functions of get_scenario_inputs.py,
run scenario.py, import_scenario_results.py, and process_results.py to run a
scenario end-to-end, i.e. get the scenario inputs from the database,
solve the scenario problem, import the results the database and perform any
necessary results-processing.

The main() function of this script can also be called with the
*gridpath_process_results* command when GridPath is installed.
"""

from argparse import ArgumentParser
import logging
import os
import signal
import sys

# GridPath modules
from db.common_functions import connect_to_database, spin_on_database_lock
from gridpath.common_functions import get_db_parser, get_solve_parser, \
    get_scenario_location_parser
from gridpath import get_scenario_inputs, run_scenario, \
    import_scenario_results, process_results


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """

    parser = ArgumentParser(
        add_help=True,
        parents=[get_db_parser(), get_scenario_location_parser(),
                 get_solve_parser()]
    )

    parsed_arguments = parser.parse_args(args=args)

    return parsed_arguments


def update_run_status(db_path, scenario, status_id):
    """
    :param db_path:
    :param scenario:
    :param status_id:
    :return:

    Update the run status in the database for the scenario.
    """

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    sql = """
        UPDATE scenarios
        SET run_status_id = ?
        WHERE scenario_name = ?;
        """

    spin_on_database_lock(conn=conn, cursor=c, sql=sql,
                          data=(status_id, scenario), many=False)


def record_process_id(db_path, scenario, process_id):
    """
    :param db_path:
    :param scenario:
    :param process_id:
    :return:

    Record the scenario run's process ID.
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    sql = """
        UPDATE scenarios
        SET run_process_id = ?
        WHERE scenario_name = ?;
        """

    spin_on_database_lock(conn=conn, cursor=c, sql=sql,
                          data=(process_id, scenario), many=False)


# TODO: add more run status types?
# TODO: handle case where scenario_name is not specified but ID is (run_scenario
#   will fail right now, as well as the update_run_status() calls (?)
# TODO: handle error messages for parser: the argparser error message will refer
#   to run_end_to_end.py, even if the parsing fails at one of the scripts
#   being called here (e.g. run_scenario.py), while the listed arguments refer
#   to the parser used when the script fails
def main(args=None):
    """

    :param args:
    :return:
    """
    # Signal-handling directives
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args)

    # Update run status to 'running'
    update_run_status(parsed_args.database, parsed_args.scenario, 1)
    # Get and record process ID
    process_id = os.getpid()
    print("Process ID is {}".format(process_id))
    record_process_id(parsed_args.database, parsed_args.scenario, process_id)

    try:
        get_scenario_inputs.main(args=args)
    except Exception as e:
        logging.exception(e)
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        print("Error encountered when getting inputs from the database for "
              "scenario {}.".format(parsed_args.scenario))
        sys.exit(1)
    try:
        run_scenario.main(args=args)
    except Exception as e:
        logging.exception(e)
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        print("Error encountered when running scenario {}.".format(
            parsed_args.scenario))
        sys.exit(1)

    try:
        import_scenario_results.main(args=args)
    except Exception as e:
        logging.exception(e)
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        print("Error encountered when importing results for "
              "scenario {}.".format(parsed_args.scenario))
        sys.exit(1)

    try:
        process_results.main(args=args)
    except Exception as e:
        logging.exception(e)
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        print('Error encountered when importing results for '
              'scenario {}.'.format(parsed_args.scenario))
        sys.exit(1)

    # If we make it here, mark run as complete
    update_run_status(parsed_args.database, parsed_args.scenario, 2)
    # TODO: should the process ID be set back to NULL?


# TODO: need to make sure that the database can be closed properly, pending
#  transactions rolled back, etc.
def exit_gracefully():
    """
    Clean up before exit
    """
    print('Exiting gracefully')
    args = sys.argv[1:]
    parsed_args = parse_arguments(args)
    update_run_status(parsed_args.database, parsed_args.scenario, 4)


def sigterm_handler(signal, frame):
    """
    Exit when SIGTERM received
    :param signal:
    :param frame:
    :return:
    """
    print("SIGTERM received by run_end_to_end.py. Terminating process.")
    exit_gracefully()
    sys.exit()


def sigint_handler(signal, frame):
    """
    Exit when SIGINT received
    :param signal:
    :param frame:
    :return:
    """
    print("SIGINT received by run_end_to_end.py. Terminating process.")
    exit_gracefully()
    sys.exit()


if __name__ == "__main__":
    main(args=sys.argv[1:])
