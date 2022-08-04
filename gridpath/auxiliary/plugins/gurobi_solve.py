import json
import sys
import gurobipy as gp
from gurobipy import GRB

import os.path

# Read and solve model

model = gp.read("/examples/test/logs/test.lp")

# Define tags for some variables in order to access their values later
for count, v in enumerate(model.getVars()):
    print(count, v)
    print(str(v)[12:-1])
    v.VTag = str(v)[12:-1]

for count, c in enumerate(model.getConstrs()):
    print(count, c)
    print(str(c)[15:-2])
    c.CTag = str(c)[15:-2]

model.setParam(GRB.Param.JSONSolDetail, 1)
model.optimize()

if model.Status == GRB.OPTIMAL:
    with open(
            "/examples/test/logs/gurobi_solution.json",
        "w",
    ) as f:
        json.dump(json.loads(model.getJSONSolution().replace("\'", '"')), f)

    # # ## TO MOVE TO run_scenario.py ###
    # scenario_directory = "/Users/ana/dev/gridpath_v0.14+dev/examples/test/"
    # solution_filename = "gurobi_solution.json"
    # with open(os.path.join(scenario_directory, "logs", solution_filename), "r") as f:
    #     solution = json.load(f)
    #
    # for v in solution["Vars"]:
    #     print(v["VTag"][0], v["X"])
    #
    # for c in solution["Constrs"]:
    #     print(c["CTag"][0], c["Pi"])
    #
    # # for c in solution("Constrs"):
    # #     print(c)

    sys.exit(0)
    
elif model.Status != GRB.INFEASIBLE:
    print("Model status: {}".format(model.Status))
    sys.exit(0)
