#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get inputs, run scenario, and import results.
"""

from argparse import ArgumentParser
import signal
import sys
import traceback

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


# TODO: add more run status types?
# TODO: handle case where scenario_name is not specified but ID is (run_scenario
#   will fail right now, as well as the update_run_status() calls (?)
# TODO: handle error messages for parser: the argparser error message will refer
#   to run_end_to_end.py, even if the parsing fails at one of the scripts
#   being called here (e.g. run_scenario.py), while the listed arguments refer
#   to the parser used when the script fails
def main(args=None):

    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args)

    update_run_status(parsed_args.database, parsed_args.scenario, 1)

    try:
        get_scenario_inputs.main(args=args)
    except Exception:
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        print("Error encountered when getting inputs from the database for "
              "scenario {}.".format(parsed_args.scenario))
        traceback.print_exc()
        sys.exit(1)
    try:
        run_scenario.main(args=args)
    except Exception:
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        print("Error encountered when running scenario {}.".format(
            parsed_args.scenario))
        traceback.print_exc()
        sys.exit(1)

    try:
        import_scenario_results.main(args=args)
    except Exception:
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        print("Error encountered when importing results for "
              "scenario {}.".format(parsed_args.scenario))
        traceback.print_exc()
        sys.exit(1)

    try:
        process_results.main(args=args)
    except Exception:
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        print('Error encountered when importing results for '
              'scenario {}.'.format(parsed_args.scenario))
        traceback.print_exc()
        sys.exit(1)

    # If we make it here, mark run as complete
    update_run_status(parsed_args.database, parsed_args.scenario, 2)


# TODO: need to make sure that the database can be closed properly, pending
#  transactions rolled back, etc.
def exit_gracefully():
    """
    Clean up before exit
    """
    print('Exiting gracefully')
    args = sys.argv[1:]
    parsed_args = parse_arguments(args)
    update_run_status(parsed_args.database, parsed_args.scenario, 3)


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
    # TODO: move these to the 'main' function after confirming behavior is
    #  the same
    # Signal-handling directives
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    main(args=sys.argv[1:])
