#!/usr/bin/env python

"""
Run model.
"""
# General
from importlib import import_module
import os.path
import sys
from csv import writer
from pandas import read_csv

# Pyomo
from pyomo.environ import *
from pyutilib.services import TempfileManager

# Scenario name
scenario_name = "test"


class ScenarioStructure(object):
    """
    Directory and file structure for the scenario.

    Check for horizon and stage subproblems, and make appropriate lists to
    iterate over.

    """
    def __init__(self, scenario):
        self.scenario_name = scenario
        self.main_scenario_directory = \
            os.path.join(os.getcwd(), "runs", scenario)

        # Check if there are horizon subproblems
        # If yes, make list of horizon subproblem names and
        # make a dictionary with the horizon subproblem name as key and
        # the horizon subproblem directory as value
        if check_for_subproblems(self.main_scenario_directory):
            self.horizon_subproblems = \
                get_subproblems(self.main_scenario_directory)
            self.horizon_subproblem_directories = \
                {h: os.path.join(self.main_scenario_directory, h)
                 for h in self.horizon_subproblems}

            # For each horizon subproblem, check if there are stage subproblems
            self.stage_subproblems = {}
            self.stage_subproblem_directories = {}
            for h in self.horizon_subproblems:
                # If there are stage subproblems, make dictionaries of stages by
                # horizon and of stage directories by horizon and stage
                if check_for_subproblems(
                        self.horizon_subproblem_directories[h]):
                    self.stage_subproblems[h] = \
                        get_subproblems(
                            self.horizon_subproblem_directories[h])
                    self.stage_subproblem_directories[h] = \
                        {s: os.path.join(
                            self.horizon_subproblem_directories[h], s)
                         for s in self.stage_subproblems[h]}
                    # Since there were subproblems in this horizon, empty the
                    # horizon subproblems list -- problems are actually by
                    # stage one level down
                    self.horizon_subproblem_directories[h] = []
                # If horizon has no stage subproblems, stages list is empty
                else:
                    self.stage_subproblems[h] = []

        # If main scenario has no horizon subproblems, horizons list is empty
        else:
            self.horizon_subproblems = []


    def make_directories(self):
        pass


def run_optimization(problem_directory):

    # TODO: move to each problem's directory
    TempfileManager.tempdir = os.path.join(os.getcwd(), "logs")

    # Create pyomo abstract model class
    model = AbstractModel()

    make_dynamic_component_objects(model)

    modules_to_use = get_modules(problem_directory)

    loaded_modules = load_modules(modules_to_use)

    populate_dynamic_component_lists(model, loaded_modules,
                                     problem_directory)

    create_abstract_model(model, loaded_modules)

    # Create a dual suffix component
    # TODO: maybe this shouldn't always be needed
    model.dual = Suffix(direction=Suffix.IMPORT)

    scenario_data = load_scenario_data(model, loaded_modules, problem_directory)

    instance = create_problem_instance(model, scenario_data)

    results = solve(instance)

    instance.solutions.load_from(results)

    save_objective_function_value(problem_directory, instance)

    save_duals(problem_directory, instance, loaded_modules)

    export_results(problem_directory, instance, loaded_modules)


# TODO: move these to load_balance and objective_function modules respectively
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


def get_modules(scenario_directory):
    """
    Modules needed for scenario
    :param scenario_directory:
    :return:
    """
    modules_file = os.path.join(scenario_directory, "modules.csv")
    try:
        modules_to_use = read_csv(modules_file)["modules"].tolist()
        return modules_to_use
    except IOError:
        print "ERROR! Modules file {} not found".format(modules_file)
        sys.exit(1)


def load_modules(modules_to_use):
    # Load modules, keep track of which modules have been imported
    loaded_modules = list()
    for m in modules_to_use:
        try:
            imported_module = import_module("."+m, package='modules')
            loaded_modules.append(imported_module)
        except ImportError:
            print("ERROR! Module " + m + " not found.")
            sys.exit(1)

    return loaded_modules


def populate_dynamic_component_lists(model, loaded_modules, problem_directory):
    inputs_directory = os.path.join(problem_directory, "inputs")
    for m in loaded_modules:
        if hasattr(m, 'determine_dynamic_components'):
            m.determine_dynamic_components(model, inputs_directory)
        else:
            pass


def create_abstract_model(model, loaded_modules):
    print("Building model...")
    for m in loaded_modules:
        if hasattr(m, 'add_model_components'):
            m.add_model_components(model)
        else:
            print("ERROR! Module " + m + " does not contain model components.")
            sys.exit(1)


def load_scenario_data(model, loaded_modules, problem_directory):
    print("Loading data...")
    # Load data
    data_portal = DataPortal()
    for m in loaded_modules:
        if hasattr(m, "load_model_data"):
            m.load_model_data(model, data_portal,
                              os.path.join(problem_directory, "inputs")
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


def export_results(problem_directory, instance, loaded_modules):
    for m in loaded_modules:
        if hasattr(m, "export_results"):
            m.export_results(problem_directory, instance)
    else:
        pass


def save_objective_function_value(problem_directory, instance):
    """
    Save the objective function value.
    :param problem_directory:
    :param instance:
    :return:
    """
    with open(os.path.join(
            problem_directory, "results", "objective_function_value.txt"),
            "w") as objective_file:
        objective_file.write(
            "Objective function: " + str(instance.Total_Cost())
        )


def save_duals(problem_directory, instance, loaded_modules):
    """
    Save the duals of various constraints.
    :param problem_directory:
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
        constraint_object = getattr(instance, c)
        duals_writer = writer(open(os.path.join(
            problem_directory, "results", str(c) + ".csv"),
            "wb"))
        duals_writer.writerow(instance.constraint_indices[c])
        for index in constraint_object:
            duals_writer.writerow(list(index) +
                            [instance.dual[constraint_object[index]]])


def check_for_subproblems(directory):
    """
    Check if more subproblems
    :param directory:
    :return:
    """
    subproblems_file = \
        os.path.join(directory, "subproblems.csv")
    if os.path.isfile(subproblems_file):
        return True
    # TODO: figure out how to know that this file SHOULD be there (currently
    # not always the case) and handle exceptions accordingly
    else:
        return False


def get_subproblems(directory):
    """
    Get names of subproblems
    :param directory:
    :return:
    """
    subproblems_file = os.path.join(directory, "subproblems.csv")
    try:
        subproblems = \
            [str(sp) for sp in read_csv(subproblems_file)["subproblems"]
                .tolist()]
        return subproblems
    except IOError:
        print """ERROR! Subproblems file {} not found""" \
            .format(subproblems_file)
        sys.exit(1)


def run_scenario(structure):
    """

    :param structure:
    :return:
    """
    # If no horizon subproblems (empty list), run main problem
    if not structure.horizon_subproblems:
        run_optimization(structure.main_scenario_directory)
    else:
        for h in structure.horizon_subproblems:
            # If no stage subproblems (empty list), run horizon problem
            if not structure.stage_subproblems[h]:
                print("Running horizon {}".format(h))
                run_optimization(structure.horizon_subproblem_directories[h])
            else:
                for s in structure.stage_subproblems[h]:
                    print("Running horizon {}, stage {}".format(h, s))
                    run_optimization(
                        structure.stage_subproblem_directories[h][s])


if __name__ == "__main__":
    scenario_structure = ScenarioStructure(scenario_name)
    run_scenario(scenario_structure)