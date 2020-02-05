import os
import sched
import subprocess
import sys
import time

from db.common_functions import connect_to_database



scheduler = sched.scheduler(time.time, time.sleep)


def check_queue(sch):
    print("Doing stuff...")
    conn = connect_to_database("/Users/ana/dev/gridpath_dev/db/io_irp.db")
    c = conn.cursor()

    scenarios_in_queue = c.execute("""
        SELECT scenario_id, scenario_name, queue_order_id, run_status_id
        FROM scenarios
        WHERE queue_order_id IS NOT NULL;
    """).fetchall()

    print("Queue:")
    for scenario in scenarios_in_queue:
        print(scenario)

    running_scenarios = c.execute("""
        SELECT run_status_id
        FROM scenarios
        WHERE queue_order_id IS NOT NULL
        AND run_status_id = 1
    """).fetchall()
    print("Running scenarios: ", running_scenarios)

    if scenarios_in_queue and not running_scenarios:
        print("No running scenarios")
        next_scenario_to_run = c.execute("""
            SELECT scenario_id, MIN(queue_order_id)
            FROM scenarios
            WHERE queue_order_id IS NOT NULL
            GROUP BY scenario_id
        """).fetchone()
        print("Next scenario to run: ", next_scenario_to_run)
        launch_scenario_process(
            db_path="/Users/ana/dev/gridpath_dev/db/io_irp.db",
            scenarios_directory="/Users/ana/dev/gridpath_dev/scenarios",
            scenario_id=next_scenario_to_run[0],
            solver="cplex",
            solver_executable="/Applications/CPLEX_Studio128/cplex/bin/x86-64_osx/cplex"
        )
    else:
        pass

    scheduler.enter(5, 1, check_queue, (sch,))


def launch_scenario_process(
    db_path, scenarios_directory, scenario_id, solver, solver_executable
):
    """
    :param db_path:
    :param scenarios_directory:
    :param scenario_id: integer, the scenario_id from the database
    :param solver: string, the solver name
    :param solver_executable: string, the solver executable
    :return:

    Launch a process to run the scenario.
    """
    # Get the scenario name for this scenario ID
    # TODO: pass both from the client and do a check here that they exist
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    scenario_name = get_scenario_name_from_scenario_id(cursor=c,
                                                       scenario_id=scenario_id)

    # First, check if the scenario is already running
    run_status, process_id = check_scenario_run_status(
        db_path=db_path,
        scenario_id=scenario_id
    )
    if run_status == 'running':
        pass
        # # This shouldn't ever happen, as the Run Scenario button should
        # # disappear when status changes to 'running'
        # print("Scenario already running.")
        # emit(
        #     "scenario_already_running"
        # )
    # If the scenario is not found among the running processes, launch a
    # process
    else:
        print("Starting process for scenario_id " + str(scenario_id))
        # Get the run_gridpath_e2e entry point script from the
        # sys.executable (remove 'python' and add 'gridpath_run_e2e')
        chars_to_remove = 10 if os.name == "nt" else 6

        run_gridpath_e2e_executable = \
            sys.executable[:-chars_to_remove] + "gridpath_run_e2e"

        p = subprocess.Popen(
            [run_gridpath_e2e_executable,
             "--log",
             "--database", db_path,
             "--scenario", scenario_name,
             "--scenario_location", scenarios_directory,
             "--solver", solver,
             "--solver_executable", solver_executable],
            shell=False
        )

        return p, scenario_id, scenario_name


def get_scenario_name_from_scenario_id(cursor, scenario_id):
    """
    :param cursor:
    :param scenario_id:
    :return:
    """
    scenario_name = cursor.execute(
        "SELECT scenario_name FROM scenarios WHERE scenario_id = {}".format(
            scenario_id
        )
    ).fetchone()[0]

    return scenario_name


def check_scenario_run_status(db_path, scenario_id):
    """
    Check if there is any running process that contains the given scenario
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()
    run_status, process_id = c.execute("""
        SELECT run_status_name, run_process_id
        FROM scenarios
        JOIN mod_run_status_types
        USING (run_status_id)
        WHERE scenario_id = {}
        """.format(scenario_id)
    ).fetchone()

    return run_status, process_id


scheduler.enter(5, 1, check_queue, (scheduler,))
scheduler.run()


