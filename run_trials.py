# Copyright 2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Run N trials and check if objective function value changes.
Note this needs to be done via subprocesses. If looping is done within a
single process, the error does not show up.
"""

from subprocess import call
import sys

SCENARIO = sys.argv[1]
N = 30

for n in range(1, N + 1):
    print(n)
    call(
        f"""python ./gridpath/run_scenario.py --scenario {SCENARIO} --scenario_location ./pyomo_examples --quiet --mute_solver_output --testing""",
        shell=True,
    )

    with open(f"./pyomo_examples/{SCENARIO}/results/objective_function_value.txt")\
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
