#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get inputs, run scenario, and import results.
"""

from argparse import ArgumentParser
import os.path
import signal
import sys
import sqlite3
import time
import traceback

# GridPath modules
from gridpath import get_scenario_inputs, run_scenario, \
    import_scenario_results, process_results


# TODO: can arguments be consolidated somehow with the other scripts
def parse_arguments(arguments):
    """
    :param arguments: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    # The database file path
    parser.add_argument("--database", help="The database file path.")

    # Scenario name and location options
    parser.add_argument("--scenario",
                        help="The name of the scenario (the same as "
                             "the directory name)")
    parser.add_argument("--scenario_location",
                        help="The path to the directory in which to create "
                             "the scenario directory.")
    # Output options
    parser.add_argument("--log", default=False, action="store_true",
                        help="Log output to a file in the logs directory as "
                             "well as the terminal.")
    parser.add_argument("--quiet", default=False, action="store_true",
                        help="Don't print run output.")

    # Solve options
    parser.add_argument("--solver", default="cbc",
                        help="Name of the solver to use. Default is cbc.")
    parser.add_argument("--mute_solver_output", default=True,
                        action="store_false",
                        help="Don't print solver output if set to true.")
    parser.add_argument("--write_solver_files_to_logs_dir", default=False,
                        action="store_true", help="Write the temporary "
                                                  "solver files to the logs "
                                                  "directory.")
    parser.add_argument("--keepfiles", default=False, action="store_true",
                        help="Save temporary solver files.")
    parser.add_argument("--symbolic", default=False, action="store_true",
                        help="Use symbolic labels in solver files.")

    # Flag for test runs (various changes in behavior)
    parser.add_argument("--testing", default=False, action="store_true",
                        help="Flag for test suite runs. Results not saved.")

    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


def update_run_status(db_path, scenario, status_id):
    """
    :param db_path:
    :param scenario:
    :param status_id:
    :return:

    Update the run status in the database for the scenario.
    """

    # Database
    # If no database is specified, assume script is run from the 'gridpath'
    # directory and the database is in ../db and named io.db
    if db_path is None:
        db_path = os.path.join(os.getcwd(), "..", "db", "io.db")

    if not os.path.isfile(db_path):
        raise OSError(
            "The database file {} was not found. Did you mean to "
            "specify a different database file?".format(
                os.path.abspath(db_path)
            )
        )

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # TODO: what's the best place for setting this
    # Allow concurrent reading and writing
    conn.execute("PRAGMA journal_mode=WAL")

    sql = """UPDATE scenarios
        SET run_status_id = {}
        WHERE scenario_name = '{}';""".format(status_id, scenario)

    spin_database_lock(
        db=conn,
        cursor=c,
        sql=sql,
        timeout=120,
        interval=1
    )


def spin_database_lock(db, cursor, sql, timeout, interval):
    for i in range(1, timeout+1):  # give up after timeout seconds
        # print("Attempt {} of {}".format(i, timeout))
        try:
            cursor.execute(sql)
            db.commit()
        except sqlite3.OperationalError as e:
            traceback.print_exc()
            if "locked" in str(e):
                print("Database is locked, sleeping for {} second, "
                      "then retrying".format(interval))
                if i == timeout - 1:
                    print("Database still locked after {} seconds. "
                          "Exiting.".format(timeout))
                    sys.exit(1)
                else:
                    time.sleep(interval)
        # Do this if exception not caught
        else:
            break


# TODO: add more run status types?
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
    print("SIGTERM received by run_start_to_end.py. Terminating process.")
    exit_gracefully()
    sys.exit()


def sigint_handler(signal, frame):
    """
    Exit when SIGINT received
    :param signal:
    :param frame:
    :return:
    """
    print("SIGINT received by run_start_to_end.py. Terminating process.")
    exit_gracefully()
    sys.exit()


if __name__ == "__main__":
    # TODO: move these to the 'main' function after confirming behavior is
    #  the same
    # Signal-handling directives
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    main(args=sys.argv[1:])
