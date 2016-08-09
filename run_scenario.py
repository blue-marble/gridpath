#!/usr/bin/env python

"""
Run model.
"""
# General
from importlib import import_module
from sys import exit

# Pyomo
from pyomo.environ import *

# Create pyomo abstract model class
model = AbstractModel()
model.energy_generation_components = list()
model.energy_consumption_components = list()
model.total_cost_components = list()

# Modules
modules_to_use = ['geography.zones', 'time.dispatch_timepoints', 'capacity.generation_capacity',
                  'operations.generation_operations',
                  'load_balance.load_balance',
                  'costs.costs']

for m in modules_to_use:
    try:
        imported_module = import_module("."+m, package='modules')
        print imported_module.__name__
    except ImportError:
        print("ERROR! Module " + m + " not found.")
        exit()
    if hasattr(imported_module, 'add_model_components'):
        imported_module.add_model_components(model)
    else:
        print("ERROR! Module does not contain model components.")
        exit()

instance = model.create_instance(data=None)

solver = SolverFactory("cbc")

print("Solving...")
solution = solver.solve(instance, tee=True)
