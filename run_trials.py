import sys
from gridpath import run_scenario

SCENARIO = sys.argv[1]
N = 300

for n in range(1, N + 1):
    # print(n)
    run_scenario_args = [
        "--scenario",
        SCENARIO,
        "--scenario_location",
        "./debug",
        "--quiet",
        "--mute_solver_output",
        "--testing",
    ]
    current_objective_value = run_scenario.main(
        args=run_scenario_args,
    )

    print(n, current_objective_value)

    if n == 1:
        previous_objective_value = current_objective_value
    else:
        if current_objective_value != previous_objective_value:
            print(f"""
                trial: {n}
                previous objective value: {previous_objective_value}
                current objective value: {current_objective_value}
            """)

        previous_objective_value = current_objective_value
