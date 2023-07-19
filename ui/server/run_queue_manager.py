from argparse import ArgumentParser
import os
import socketio
import sys
import time

from db.common_functions import connect_to_database, spin_on_database_lock


def exit_gracefully():
    print("Exiting gracefully")
    args = sys.argv[1:]
    parsed_args = parse_arguments(args)

    conn = connect_to_database(db_path=parsed_args.database)
    c = conn.cursor()

    sql = """
        UPDATE scenarios SET queue_order_id = NULL;
    """
    conn.commit()

    spin_on_database_lock(conn=conn, cursor=c, sql=sql, data=(), many=False)


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
                    next_scenario_to_run = c.execute(
                        """
                        SELECT scenario_id, MIN(queue_order_id)
                        FROM scenarios
                        WHERE queue_order_id IS NOT NULL
                        GROUP BY scenario_id
                    """
                    ).fetchone()

                    # Get the requested solver
                    solver_options_id = c.execute(
                        """
                        SELECT solver_options_id
                            FROM scenarios
                            WHERE scenario_id = {}
                    """.format(
                            next_scenario_to_run[0]
                        )
                    ).fetchone()[0]

                    if solver_options_id is None:
                        # TODO: we should specify the default solver as a
                        #  global variable somewhere
                        solver = "cbc"
                    else:
                        solver_query = c.execute(
                            """
                              SELECT DISTINCT solver_name
                              FROM inputs_options_solver
                              WHERE solver_options_id = {};
                              """.format(
                                solver_options_id
                            )
                        ).fetchone()
                        # Check that there's only one solver specified for the
                        # solver_options_id
                        one_solver_check = c.execute(
                            """
                              SELECT COUNT()
                              FROM (
                                  SELECT DISTINCT solver_name
                                  FROM inputs_options_solver
                                  WHERE solver_options_id = {}
                                  )
                              ;
                              """.format(
                                solver_options_id
                            )
                        ).fetchone()[0]
                        if one_solver_check > 1:
                            raise ValueError(
                                """
                              Only one solver name can be specified per
                              solver_options_id. Check the solver_options_id {}
                              in the the inputs_options_solver table.
                            """.format(
                                    solver_options_id
                                )
                            )
                        else:
                            solver = solver_query[0]
                    sio.emit(
                        "launch_scenario_process",
                        {
                            "scenario": next_scenario_to_run[0],
                            "solver": solver,
                            "skipWarnings": False,
                        },
                    )
            # If there are no scenarios in the queue, tell the server to
            # reset the queue manager PID and exit the loop
            # TODO: is keeping track of the queue manager PID still needed
            #  now that the queue manager exits when it does not get a
            #  response from the server?
            else:
                sio.emit("reset_queue_manager_pid")
                break

        except socketio.exceptions.ConnectionError:
            print("Server not responding, exiting")
            break

        time.sleep(5)

    # Need os._exit(0) to exit process, not just thread (sys.exit exits only
    # current thread)
    # https://stackoverflow.com/questions/73663/terminating-a-python-script
    # https://stackoverflow.com/questions/905189/why-does-sys-exit-not-exit-when-called-inside-a-thread-in-python/5120178#5120178
    print("Broke out of while loop and trying to exit")
    exit_gracefully()
    os._exit(0)


def get_scenarios_in_queue(c):
    # Check if there are any scenarios in the queue
    scenarios_in_queue = c.execute(
        """
        SELECT scenario_id, scenario_name, queue_order_id, run_status_id
        FROM scenarios
        WHERE queue_order_id IS NOT NULL;
    """
    ).fetchall()

    return scenarios_in_queue


def get_running_scenarios(c):
    # Get the scenarios from the queue that are currently running
    running_scenarios = c.execute(
        """
        SELECT scenario_id, scenario_name, run_status_id
        FROM scenarios
        WHERE queue_order_id IS NOT NULL
        AND run_status_id = 1
    """
    ).fetchall()

    return running_scenarios


def get_max_queue_order_id(c):
    max_queue_id = c.execute(
        """
        SELECT max(queue_order_id)
        FROM scenarios;
    """
    ).fetchone()[0]

    if max_queue_id is None:
        max_queue_id = 0

    return max_queue_id


def add_scenario_to_queue(db_path, scenario_id):
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    next_queue_id = get_max_queue_order_id(c=c) + 1

    sql = """
        UPDATE scenarios
        SET queue_order_id = ?,
        run_status_id = 5
        WHERE scenario_id = ?;
    """

    spin_on_database_lock(
        conn=conn, cursor=c, sql=sql, data=(next_queue_id, scenario_id), many=False
    )


def remove_scenario_from_queue(db_path, scenario_id):
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    sql = """
        UPDATE scenarios
        SET queue_order_id = NULL,
        run_status_id = 0
        WHERE scenario_id = ?;
    """

    spin_on_database_lock(conn=conn, cursor=c, sql=sql, data=(scenario_id,), many=False)


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """

    parser = ArgumentParser(add_help=True)
    parser.add_argument(
        "--database",
        default="../db/io.db",
        help="The database file path. Defaults to ../db/io.db " "if not specified",
    )

    parsed_arguments = parser.parse_args(args=args)

    return parsed_arguments


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args)

    manage_queue(db_path=parsed_args.database)


if __name__ == "__main__":
    main()
