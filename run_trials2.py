from subprocess import call
import sys

SCENARIO = sys.argv[1]
N = 100

for n in range(1, N + 1):
    print(n)
    call(
        f"""python ./gridpath/run_scenario.py --scenario {SCENARIO} --scenario_location ./debug --quiet --mute_solver_output --testing""",
        shell=True,
    )

    with open(f"./debug/{SCENARIO}/results/objective_function_value.txt")\
            as f:
        current_objective_value = float(f.read())

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
