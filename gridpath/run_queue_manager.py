import sched
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

    for scenario in scenarios_in_queue:
        print(scenario)

    scheduler.enter(5, 1, check_queue, (sch,))


scheduler.enter(5, 1, check_queue, (scheduler,))
scheduler.run()
