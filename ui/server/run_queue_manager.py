import sched
import time

from db.common_functions import connect_to_database
from ui.server.scenario_process import launch_scenario_process

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


scheduler.enter(5, 1, check_queue, (scheduler,))
scheduler.run()


