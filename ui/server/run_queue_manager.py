from argparse import ArgumentParser
import os
import socketio
import signal
import sys
import time

from db.common_functions import connect_to_database


# TODO: how should we do this on Windows
# If we have runs in the queue, they need to be removed when forcing this
# process to close (e.g. when exiting the UI)
def exit_gracefully():
    print('Exiting gracefully')
    args = sys.argv[1:]
    parsed_args = parse_arguments(args)

    conn = connect_to_database(db_path=parsed_args.database)
    c = conn.cursor()

    # TODO: use spin on database lock
    c.execute("""
        UPDATE scenarios SET queue_order_id = NULL;
    """)
    conn.commit()


# Define custom signal handlers
def sigterm_handler(signal, frame):
    """
    Exit when SIGTERM received (we're sending SIGTERM from Electron on app
    exit)
    :param signal:
    :param frame:
    :return:
    """
    print('SIGTERM received by queue manager. Terminating queue manager '
          'process.')
    # exit_gracefully()
    # sys.exit(0)
    pass


def sigint_handler(signal, frame):
    """
    Exit when SIGINT received
    :param signal:
    :param frame:
    :return:
    """
    print('SIGINT received by queue manager. Terminating queue manager '
          'process.')
    exit_gracefully()
    sys.exit(0)


def manage_queue(db_path):
    while True:
        try:
            # Check if server is running
            sio = socketio.Client()
            sio.connect("http://127.0.0.1:8080")
            print("Connection to server established")

            conn = connect_to_database(db_path=db_path)
            c = conn.cursor()

            scenarios_in_queue = get_scenarios_in_queue(c=c)
            running_scenarios = get_running_scenarios(c=c)

            # If there are scenarios in the queue and none of them are running,
            # get the next scenarios to run and launch it
            if scenarios_in_queue:  # there are scenarios in the queue
                if not running_scenarios:  # none of them is 'running'
                    next_scenario_to_run = c.execute("""
                        SELECT scenario_id, MIN(queue_order_id)
                        FROM scenarios
                        WHERE queue_order_id IS NOT NULL
                        GROUP BY scenario_id
                    """).fetchone()

                    # # Get the requested solver
                    solver = c.execute("""
                        SELECT name
                        FROM options_solver_descriptions
                        WHERE solver_options_id = (
                            SELECT solver_options_id
                            FROM scenarios
                            WHERE scenario_id = {}
                            );
                        """.format(next_scenario_to_run[0])
                                       ).fetchone()[0]
                    sio.emit(
                        "launch_scenario_process",
                        {"scenario": next_scenario_to_run[0], "solver": solver,
                         "skipWarnings": False}
                    )
                else:
                    pass
            else:
                # sio.emit("stop_queue_manager")
                # sys.exit(0)
                pass

        except socketio.exceptions.ConnectionError:
            print("Server not responding, exiting")
            break

        time.sleep(5)

    print("Broke out of while loop and trying to exit")
    os._exit(0)


    # scheduler.enter(5, 1, manage_queue, (sch,))


def get_scenarios_in_queue(c):
    # Check if there are any scenarios in the queue
    scenarios_in_queue = c.execute("""
        SELECT scenario_id, scenario_name, queue_order_id, run_status_id
        FROM scenarios
        WHERE queue_order_id IS NOT NULL;
    """).fetchall()

    return scenarios_in_queue


def get_running_scenarios(c):
    # Get the scenarios from the queue that are currently running
    running_scenarios = c.execute("""
        SELECT scenario_id, scenario_name, run_status_id
        FROM scenarios
        WHERE queue_order_id IS NOT NULL
        AND run_status_id = 1
    """).fetchall()

    return running_scenarios


def get_max_queue_order_id(c):
    max_queue_id = c.execute("""
        SELECT max(queue_order_id)
        FROM scenarios;
    """).fetchone()[0]

    if max_queue_id is None:
        max_queue_id = 0

    return max_queue_id


def add_scenario_to_queue(db_path, scenario_id):
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    next_queue_id = get_max_queue_order_id(c=c) + 1

    # TODO: use spin_on_database_lock
    c.execute("""
        UPDATE scenarios
        SET queue_order_id = {},
        run_status_id = 5
        WHERE scenario_id = {};
    """.format(next_queue_id, scenario_id))

    conn.commit()


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """

    parser = ArgumentParser(add_help=True)
    parser.add_argument("--database", default="../db/io_irp.db",
                        help="The database file path. Defaults to ../db/io.db "
                             "if not specified")

    parsed_arguments = parser.parse_args(args=args)

    return parsed_arguments


def main(args=None):
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args)

    manage_queue(db_path=parsed_args.database)


if __name__ == "__main__":
    main()


