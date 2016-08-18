#!/usr/bin/env python

"""
Run model.
"""
# General
from importlib import import_module
import sys
import os
import csv

# Pyomo
from pyomo.environ import *
from pyutilib.services import TempfileManager

# Scenario name
scenario_name = "test"


def run_scenario(scenario):

    TempfileManager.tempdir = os.path.join(os.getcwd(), "logs")

    # Create pyomo abstract model class
    model = AbstractModel()

    make_dynamic_component_objects(model)

    modules_to_use = get_modules()

    loaded_modules = load_modules(modules_to_use)

    populate_dynamic_component_lists(model, loaded_modules, scenario)

    create_abstract_model(model, loaded_modules)

    # Create a dual suffix component
    # TODO: maybe this shouldn't always be needed
    model.dual = Suffix(direction=Suffix.IMPORT)

    scenario_data = load_scenario_data(model, loaded_modules, scenario)

    instance = create_problem_instance(model, scenario_data)

    results = solve(instance)

    instance.solutions.load_from(results)

    save_objective_function_value(scenario, instance)

    save_duals(scenario, instance, loaded_modules)

    export_results(instance, loaded_modules)


def make_dynamic_component_objects(model):
    """
    Lists of model components that modules will populate
    :param model:
    :return:
    """
    # Load balance
    # TODO: these may have to vary by load area
    model.energy_generation_components = list()
    model.energy_consumption_components = list()

    # Objective function
    model.total_cost_components = list()


def get_modules():
    # Modules/
    # TODO: read from file
    modules_to_use = ['geography.zones', 'time.dispatch_timepoints',
                      'generation.capacity.generation_capacity',
                      'generation.operations.services',
                      'generation.operations.operations',
                      'system.load_balance.load_balance',
                      'system.reserves.lf_reserves_up',
                      'system.reserves.regulation_up',
                      'system.reserves.lf_reserves_down',
                      'system.reserves.regulation_down',
                      'objective.min_total_cost']

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
            m.determine_dynamic_components(model,
                                           os.path.join(os.getcwd(),
                                                        "runs",
                                                        scenario,
                                                        "inputs")
                                           )
        else:
            pass


def create_abstract_model(model, loaded_modules):
    print("Building model...")
    for m in loaded_modules:
        if hasattr(m, 'add_model_components'):
            m.add_model_components(model)
        else:
            print("ERROR! Module " + m + " does not contain model components.")
            sys.exit()


def load_scenario_data(model, loaded_modules, scenario):
    print("Loading data...")
    # Load data
    data_portal = DataPortal()
    for m in loaded_modules:
        if hasattr(m, "load_model_data"):
            m.load_model_data(model, data_portal,
                              os.path.join(os.getcwd(),
                                           "runs",
                                           scenario,
                                           "inputs")
                              )
        else:
            pass
    return data_portal


def create_problem_instance(model, loaded_data):
    print("Creating problem instance...")
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
    results = solver.solve(instance,
                           tee=True,
                           keepfiles=False,
                           symbolic_solver_labels=False
                           )
    return results


def export_results(instance, loaded_modules):
    for m in loaded_modules:
        if hasattr(m, "export_results"):
            m.export_results(instance)
    else:
        pass


def save_objective_function_value(scenario, instance):
    """
    Save the objective function value.
    :param scenario:
    :param instance:
    :return:
    """
    with open(os.path.join(
            os.path.join(os.getcwd(), "runs", scenario, "results"),
            "objective_function_value.txt"), "w"
    ) as objective_file:
        objective_file.write(
            "Objective function: " + str(instance.Total_Cost())
        )


def save_duals(scenario, instance, loaded_modules):
    """
    Save the duals of various constraints.
    :param scenario:
    :param instance:
    :param loaded_modules:
    :return:
    """

    instance.constraint_indices = {}
    for m in loaded_modules:
        if hasattr(m, "save_duals"):
            m.save_duals(instance)
        else:
            pass

    for c in instance.constraint_indices.keys():
        print c
        constraint_object = getattr(instance, c)
        print constraint_object
        writer = csv.writer(open(os.path.join(
            os.getcwd(), "runs", scenario, "results", str(c) + ".csv"), "wb"))
        writer.writerow(instance.constraint_indices[c])
        for index in constraint_object:
            writer.writerow(list(index) +
                            [instance.dual[constraint_object[index]]])

if __name__ == "__main__":
    run_scenario(scenario_name)