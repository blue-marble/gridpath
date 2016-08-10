#!/usr/bin/env python

"""
Run model.
"""
# General
from importlib import import_module
import sys
import os

# Pyomo
from pyomo.environ import *

# Scenario name
scenario_name = "test"


def run_scenario(scenario):
    # Create pyomo abstract model class
    model = AbstractModel()

    make_dynamic_component_objects(model)

    modules_to_use = get_modules()

    loaded_modules = load_modules(modules_to_use)

    populate_dynamic_component_lists(model, loaded_modules, scenario)

    create_abstract_model(model, loaded_modules)

    scenario_data = load_scenario_data(model, loaded_modules, scenario)

    instance = create_problem_instance(model, scenario_data)

    solve(instance)

    export_results(instance, loaded_modules)


def make_dynamic_component_objects(model):
    """
    Lists of model components that modules will populate
    :param model:
    :return:
    """
    # Generator capabilities
    model.headroom_variables = dict()

    # Load balance
    # TODO: these may have to vary by load area
    model.energy_generation_components = list()
    model.energy_consumption_components = list()

    # Reserves
    model.upward_reserve_components = list()
    model.downward_reserve_components = list()

    # Objective function
    model.total_cost_components = list()


def get_modules():
    # Modules
    # TODO: read from file
    modules_to_use = ['geography.zones', 'time.dispatch_timepoints', 'capacity.generation_capacity',
                      'operations.generation_operations',
                      'load_balance.load_balance',
                      'reserves.reserve_requirements',
                      'costs.costs']

    return modules_to_use


def load_modules(modules_to_use):
    # Load modules, keep track of which modules have been imported
    loaded_modules = list()
    for m in modules_to_use:
        try:
            imported_module = import_module("."+m, package='modules')
            loaded_modules.append(imported_module)
        except ImportError:
            print("ERROR! Module " + m + " not found.")
            sys.exit()

    return loaded_modules


def populate_dynamic_component_lists(model, loaded_modules, scenario):
    for m in loaded_modules:
        if hasattr(m, 'determine_dynamic_components'):
            m.determine_dynamic_components(model, os.path.join(os.getcwd(), "runs", scenario, "inputs"))
        else:
            pass


def create_abstract_model(model, loaded_modules):
    for m in loaded_modules:
        if hasattr(m, 'add_model_components'):
            m.add_model_components(model)
        else:
            print("ERROR! Module does not contain model components.")
            sys.exit()


def load_scenario_data(model, loaded_modules, scenario):
    # Load data
    data_portal = DataPortal()
    for m in loaded_modules:
        if hasattr(m, "load_model_data"):
            m.load_model_data(model, data_portal, os.path.join(os.getcwd(), "runs", scenario, "inputs"))
        else:
            pass
    return data_portal


def create_problem_instance(model, loaded_data):
    # Create instance
    instance = model.create_instance(loaded_data)
    return instance


def view_loaded_data(loaded_modules, instance):
    """
    View data (for debugging)
    :param loaded_modules:
    :param instance:
    :return:
    """
    for m in loaded_modules:
        if hasattr(m, "view_loaded_data"):
            m.view_loaded_data(instance)


def solve(instance):
    # Get solver and solve
    solver = SolverFactory("cbc")

    print("Solving...")
    solver.solve(instance, tee=True)


def export_results(instance, loaded_modules):
    for m in loaded_modules:
        if hasattr(m, "export_results"):
            m.export_results(instance)
    else:
        pass

if __name__ == "__main__":
    run_scenario(scenario_name)