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
import datetime
import logging
import os
import signal
import sys

# GridPath modules
from db.common_functions import connect_to_database, spin_on_database_lock
from gridpath.common_functions import get_db_parser, get_solve_parser, \
    get_scenario_location_parser, create_logs_directory_if_not_exists,\
    Logging, determine_scenario_directory
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


# TODO: change all these to use scenario_id, not scenario_name
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


def record_process_id_and_start_time(db_path, scenario, process_id, start_time):
    """
    :param db_path:
    :param scenario:
    :param process_id:
    :param start_time:
    :return:

    Record the scenario run's process ID.
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    sql = """
        UPDATE scenarios
        SET run_process_id = ?,
        run_start_time = ?
        WHERE scenario_name = ?;
        """

    spin_on_database_lock(
        conn=conn, cursor=c, sql=sql,
        data=(process_id, start_time, scenario),
        many=False
    )


def record_end_time(db_path, scenario, process_id, end_time):
    """
    :param db_path:
    :param scenario:
    :param process_id:
    :param end_time:
    :return:

    Record the scenario run's process ID.
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    sql = """
        UPDATE scenarios
        SET run_end_time = ?
        WHERE scenario_name = ?
        AND run_process_id = ?;
        """

    spin_on_database_lock(
        conn=conn, cursor=c, sql=sql,
        data=(end_time, scenario, process_id),
        many=False
    )


def check_if_in_queue(db_path, scenario):
    # Check if we're running from the queue
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    queue_order_id = c.execute(
        """
        SELECT queue_order_id
        FROM scenarios
        WHERE scenario_name = '{}'
        """.format(scenario)
    ).fetchone()[0]

    return queue_order_id


def remove_from_queue_if_in_queue(db_path, scenario, queue_order_id):
    # If running from the queue, remove from the queue

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    if queue_order_id is not None:
        print("Removing scenario ID {} from queue".format(scenario))
        sql = """
            UPDATE scenarios SET queue_order_id = NULL WHERE scenario_name = ?
        """
        spin_on_database_lock(
            conn=conn, cursor=c, sql=sql,
            data=(scenario,),
            many=False
        )
    else:
        pass



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

    # Get process ID and start_time
    process_id = os.getpid()
    start_time = datetime.datetime.now()

    # Signal-handling directives
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args)

    # Log the run if requested
    # If directed to do so, log e2e run
    scenario_directory = determine_scenario_directory(
        scenario_location=parsed_args.scenario_location,
        scenario_name=parsed_args.scenario
    )
    if parsed_args.log:
        logs_directory = create_logs_directory_if_not_exists(
            scenario_directory=scenario_directory,
            subproblem="", stage="")

        # Save sys.stdout so we can return to it later
        stdout_original = sys.stdout
        stderr_original = sys.stderr

        # The print statement will call the write() method of any object
        # you assign to sys.stdout (in this case the Logging object). The
        # write method of Logging writes both to sys.stdout and a log file
        # (see auxiliary/auxiliary.py)
        logger = Logging(
            logs_dir=logs_directory,
            start_time=start_time,
            e2e=True,
            process_id=process_id
        )
        sys.stdout = logger
        sys.stderr = logger

    print("Running scenario {} end to end".format(parsed_args.scenario))

    # Check if running from queue
    queue_order_id = check_if_in_queue(
        parsed_args.database, parsed_args.scenario
    )

    # Update run status to 'running'
    update_run_status(parsed_args.database, parsed_args.scenario, 1)

    # Record process ID and process start time in database
    print("Process ID is {}".format(process_id))
    print("End-to-end run started on {}".format(start_time))
    record_process_id_and_start_time(
        parsed_args.database, parsed_args.scenario, process_id, start_time
    )

    try:
        get_scenario_inputs.main(args=args)
    except Exception as e:
        logging.exception(e)
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        remove_from_queue_if_in_queue(
            parsed_args.database, parsed_args.scenario, queue_order_id
        )
        print("Error encountered when getting inputs from the database for "
              "scenario {}.".format(parsed_args.scenario))
        sys.exit(1)
    try:
        run_scenario.main(args=args)
    except Exception as e:
        logging.exception(e)
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        remove_from_queue_if_in_queue(
            parsed_args.database, parsed_args.scenario, queue_order_id
        )
        print("Error encountered when running scenario {}.".format(
            parsed_args.scenario))
        sys.exit(1)

    try:
        import_scenario_results.main(args=args)
    except Exception as e:
        logging.exception(e)
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        remove_from_queue_if_in_queue(
            parsed_args.database, parsed_args.scenario, queue_order_id
        )
        print("Error encountered when importing results for "
              "scenario {}.".format(parsed_args.scenario))
        sys.exit(1)

    try:
        process_results.main(args=args)
    except Exception as e:
        logging.exception(e)
        update_run_status(parsed_args.database, parsed_args.scenario, 3)
        remove_from_queue_if_in_queue(
            parsed_args.database, parsed_args.scenario, queue_order_id
        )
        print('Error encountered when importing results for '
              'scenario {}.'.format(parsed_args.scenario))
        sys.exit(1)

    # If we make it here, mark run as complete and update run end time
    end_time = datetime.datetime.now()
    update_run_status(parsed_args.database, parsed_args.scenario, 2)
    remove_from_queue_if_in_queue(
        parsed_args.database, parsed_args.scenario, queue_order_id
    )
    record_end_time(
        db_path=parsed_args.database, scenario=parsed_args.scenario,
        process_id=process_id, end_time=end_time
    )
    # TODO: should the process ID be set back to NULL?

    print("Done. Run finished on {}.".format(end_time))

    # If logging, we need to return sys.stdout to original (i.e. stop writing
    # to log file)
    if parsed_args.log:
        sys.stdout = stdout_original
        sys.stderr = stderr_original


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
