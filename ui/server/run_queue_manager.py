from socketio import Client
import sched
import time

from db.common_functions import connect_to_database
from ui.server.scenario_process import launch_scenario_process


# # Global server variables
# SCENARIOS_DIRECTORY = os.environ['SCENARIOS_DIRECTORY']
# # DATABASE_PATH = '/Users/ana/dev/ui-run-scenario/db/io.db'
# DATABASE_PATH = os.environ['GRIDPATH_DATABASE_PATH']
# SOLVER1_NAME = os.environ['SOLVER1_NAME']
# SOLVER1_EXECUTABLE = os.environ['SOLVER1_EXECUTABLE']
# SOLVER2_NAME = os.environ['SOLVER2_NAME']
# SOLVER2_EXECUTABLE = os.environ['SOLVER2_EXECUTABLE']
# SOLVER3_NAME = os.environ['SOLVER3_NAME']
# SOLVER3_EXECUTABLE = os.environ['SOLVER3_EXECUTABLE']
# SOLVERS = {
#   SOLVER1_NAME: SOLVER1_EXECUTABLE,
#   SOLVER2_NAME: SOLVER2_EXECUTABLE,
#   SOLVER3_NAME: SOLVER3_EXECUTABLE
# }

# Make scheduler object
scheduler = sched.scheduler(time.time, time.sleep)


def manage_queue(sch):
    conn = connect_to_database("/Users/ana/dev/gridpath_dev/db/io_irp.db")
    c = conn.cursor()

    # Check if there are any scenarios in the queue
    scenarios_in_queue = c.execute("""
        SELECT scenario_id, scenario_name, queue_order_id, run_status_id
        FROM scenarios
        WHERE queue_order_id IS NOT NULL;
    """).fetchall()

    # Get the scenarios from the queue that are currently running
    running_scenarios = c.execute("""
        SELECT scenario_id, scenario_name, run_status_id
        FROM scenarios
        WHERE queue_order_id IS NOT NULL
        AND run_status_id = 1
    """).fetchall()

    # If there are scenarios in the queue and none of them are running,
    # get the next scenarios to run and launch it
    if scenarios_in_queue and not running_scenarios:
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

        # TODO: should we ping back the server function instead of launching
        #  here?
        # launch_scenario_process(
        #     db_path=db_path,
        #     scenarios_directory=scenarios_directory,
        #     scenario_id=next_scenario_to_run[0],
        #     solver=solver,
        #     solver_executable=solver_executable
        # )
        sio.emit(
            "launch_scenario_process",
            {"scenario": next_scenario_to_run[0], "solver": solver,
             "skipWarnings": False}
        )
    else:
        pass

    scheduler.enter(5, 1, manage_queue, (sch,))


if __name__ == "__main__":
    sio = Client()
    sio.connect("http://127.0.0.1:8080")
    print("Connection to server established")
    scheduler.enter(5, 1, manage_queue, (scheduler,))
    scheduler.run()


