# Copyright 2016-2023 Blue Marble Analytics LLC.
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
Solve from LP file with Gurobi and save GridPath-compatible solution file.
"""

import json
import sys
import gurobipy
import os.path

from gridpath.auxiliary.plugins.common_functions import parse_arguments


def main(args=None):
    if args is None:
        args = sys.argv[1:]
        parsed_args = parse_arguments(arguments=args)

        prob_sol_dir = parsed_args.problem_file_directory
        problem_file = parsed_args.problem_file_name

        # Read model
        model = gurobipy.read(os.path.join(prob_sol_dir, problem_file))

        # Define tags for some variables in order to access their values later
        for count, v in enumerate(model.getVars()):
            v.VTag = str(v)[12:-1]

        for count, c in enumerate(model.getConstrs()):
            c.CTag = str(c)[15:-2]

        model.setParam(gurobipy.GRB.Param.JSONSolDetail, 1)
        model.optimize()

        if model.Status == gurobipy.GRB.OPTIMAL:
            with open(
                os.path.join(prob_sol_dir, "gurobi_solution.json"),
                "w",
            ) as f:
                json.dump(json.loads(model.getJSONSolution().replace("'", '"')), f)

            sys.exit(0)

        elif model.Status != gurobipy.GRB.INFEASIBLE:
            print("Model was infeasible. Status: {}".format(model.Status))
            sys.exit(0)


if __name__ == "__main__":
    main()
