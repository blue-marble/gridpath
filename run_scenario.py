#!/usr/bin/env python

"""
Run model.
"""
from argparse import ArgumentParser
import os.path
import sys
from csv import writer
from importlib import import_module

from pandas import read_csv
from pyomo.environ import *
from pyutilib.services import TempfileManager

from modules.auxiliary.dynamic_components import DynamicComponents


class ScenarioStructure(object):
    """
    Directory and file structure for the scenario.

    Check for horizon and stage subproblems, and make appropriate lists to
    iterate over and solve each subproblem.

    """
    def __init__(self, scenario, scenario_location):
        self.main_scenario_directory = \
            os.path.join(os.getcwd(), scenario_location, scenario)

        # Check if there are horizon subproblems
        # If yes, make list of horizon subproblem names and
        # make a dictionary with the horizon subproblem name as key and
        # the horizon subproblem directory as value
        if check_for_subproblems(self.main_scenario_directory):
            self.horizons_flag = True
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
                    self.stages_flag = True
                    self.stage_subproblems[h] = \
                        get_subproblems(
                            self.horizon_subproblem_directories[h])
                    self.stage_subproblem_directories[h] = \
                        {s: os.path.join(
                            self.horizon_subproblem_directories[h], s)
                         for s in self.stage_subproblems[h]}
                    # Create the commitment pass-through file (also deletes any
                    # prior results)
                    # TODO: need better handling of deleting prior results?
                    with open(
                            os.path.join(
                                self.horizon_subproblem_directories[h],
                            "pass_through_inputs",
                                "fixed_commitment.tab"), "wb") \
                            as fixed_commitment_file:
                        fixed_commitment_writer = \
                            writer(fixed_commitment_file, delimiter="\t")
                        fixed_commitment_writer.writerow(
                            ["project", "timepoint", "final_stage",
                             "commitment"])

                    # Since there were subproblems in this horizon, empty the
                    # horizon subproblems list -- problems are actually by
                    # stage one level down
                    self.horizon_subproblem_directories[h] = []
                # If horizon has no stage subproblems, stages list is empty
                else:
                    self.stages_flag = False
                    self.stage_subproblems[h] = []

        # If main scenario has no horizon subproblems, horizons list is empty
        else:
            self.horizons_flag = False
            self.horizon_subproblems = []


def run_optimization(scenario_directory, horizon, stage, parsed_arguments):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param parsed_arguments:
    :return:
    """

    # TODO: how best to handle non-empty results directories?
    # Make results and logs directories
    results_directory = os.path.join(scenario_directory, horizon, stage,
                                     "results")
    logs_directory = os.path.join(scenario_directory, horizon, stage,
                                  "logs")
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
    # Write temporary files to logs directory
    TempfileManager.tempdir = logs_directory

    # Create pyomo abstract model class
    model = AbstractModel()

    # Initialize the dynamic components class
    dynamic_inputs = DynamicComponents()

    modules_to_use = get_modules(scenario_directory)

    loaded_modules = load_modules(modules_to_use)

    # Set dynamic components as attributes to inputs class
    populate_dynamic_components(dynamic_inputs, loaded_modules,
                                scenario_directory, horizon, stage)

    # Create the abstract model; some components are initialized here
    create_abstract_model(model, dynamic_inputs,
                          scenario_directory, horizon, stage,
                          loaded_modules)

    # Create a dual suffix component
    # TODO: maybe this shouldn't always be needed
    model.dual = Suffix(direction=Suffix.IMPORT)

    # Load the scenario data
    scenario_data = load_scenario_data(model, dynamic_inputs, loaded_modules,
                                       scenario_directory, horizon, stage)

    # Build the problem instance; this will also call any BuildActions that
    # construct the dynamic inputs
    instance = create_problem_instance(model, scenario_data)

    # Fix variables if modules request so
    instance = fix_variables(instance, dynamic_inputs, loaded_modules)

    # Solve
    results = solve(instance, parsed_arguments)

    # RESULTS
    instance.solutions.load_from(results)

    save_objective_function_value(scenario_directory, horizon, stage, instance)

    save_duals(scenario_directory, horizon, stage, instance, loaded_modules)

    export_results(scenario_directory, horizon, stage, instance, dynamic_inputs,
                   loaded_modules)


def get_modules(scenario_directory):
    """
    Modules needed for scenario
    :param scenario_directory:
    :return:
    """
    modules_file = os.path.join(scenario_directory, "modules.csv")
    try:
        requested_modules = read_csv(modules_file)["modules"].tolist()
    except IOError:
        print "ERROR! Modules file {} not found".format(modules_file)
        sys.exit(1)

    # If all optional modules are selected, this would be the list
    all_modules = [
        "temporal.operations.timepoints",
        "temporal.operations.horizons",
        "temporal.investment.periods",
        "geography.load_zones",
        "geography.load_following_up_balancing_areas",
        "geography.load_following_down_balancing_areas",
        "geography.regulation_up_balancing_areas",
        "geography.regulation_down_balancing_areas",
        'project',
        "project.capacity.capacity",
        "project.capacity.costs",
        "project.operations.reserves.lf_reserves_up",
        "project.operations.reserves.lf_reserves_down",
        "project.operations.reserves.regulation_up",
        "project.operations.reserves.regulation_down",
        "project.operations.fuels",
        "project.operations.operations",
        "project.operations.fix_commitment",
        "project.operations.costs",
        "transmission",
        "transmission.capacity.capacity",
        "transmission.operations.operations",
        "system.load_balance.load_balance",
        "system.load_balance.costs",
        "system.reserves.lf_reserves_up",
        "system.reserves.regulation_up",
        "system.reserves.lf_reserves_down",
        "system.reserves.regulation_down",
        "policy.rps",
        "objective.min_total_cost"
    ]

    # Names of groups of optional modules
    optional_modules = {
        "fuels":
            ["project.operations.fuels"],
        "multi_stage":
            ["project.operations.fix_commitment"],
        "transmission":
            ["transmission",
             "transmission.capacity.capacity",
             "transmission.operations.operations"],
        "lf_reserves_up":
            ["geography.load_following_up_balancing_areas",
             "project.operations.reserves.lf_reserves_up",
             "system.reserves.lf_reserves_up"],
        "lf_reserves_down":
            ["geography.load_following_down_balancing_areas",
            "project.operations.reserves.lf_reserves_down",
             "system.reserves.lf_reserves_down"],
        "regulation_up":
            ["geography.regulation_up_balancing_areas",
             "project.operations.reserves.regulation_up",
             "system.reserves.regulation_up"],
        "regulation_down":
            ["geography.regulation_down_balancing_areas",
             "project.operations.reserves.regulation_down",
             "system.reserves.regulation_down"],
        "rps":
            ["policy.rps"]
    }

    # Remove any modules not requested by user
    modules_to_use = all_modules
    for module_name in optional_modules.keys():
        if module_name in requested_modules:
            pass
        else:
            for m in optional_modules[module_name]:
                modules_to_use.remove(m)

    return modules_to_use


def load_modules(modules_to_use):
    # Load modules, keep track of which modules have been imported
    loaded_modules = list()
    for m in modules_to_use:
        try:
            imported_module = import_module("."+m, package='modules')
            loaded_modules.append(imported_module)
        except ImportError:
            print("ERROR! Module " + str(m) + " not found.")
            sys.exit(1)

    return loaded_modules


def populate_dynamic_components(inputs, loaded_modules,
                                scenario_directory, horizon, stage):
    for m in loaded_modules:
        if hasattr(m, 'determine_dynamic_components'):
            m.determine_dynamic_components(inputs,
                                           scenario_directory, horizon, stage)
        else:
            pass


def create_abstract_model(model, inputs, scenario_directory, horizon, stage,
                          loaded_modules):
    print("Building model...")
    for m in loaded_modules:
        if hasattr(m, 'add_model_components'):
            m.add_model_components(model, inputs)


def load_scenario_data(model, dynamic_inputs, loaded_modules,
                       scenario_directory, horizon, stage):
    print("Loading data...")
    # Load data
    data_portal = DataPortal()
    for m in loaded_modules:
        if hasattr(m, "load_model_data"):
            m.load_model_data(model, dynamic_inputs, data_portal,
                              scenario_directory, horizon, stage)
        else:
            pass
    return data_portal


def create_problem_instance(model, loaded_data):
    print("Creating problem instance...")
    # Create instance
    instance = model.create_instance(loaded_data)
    return instance


def fix_variables(instance, dynamic_inputs, loaded_modules):
    """
    Fix any variables modules want fixed and return the modified instance
    :param instance:
    :param dynamic_inputs:
    :param loaded_modules:
    :return:
    """
    for m in loaded_modules:
        if hasattr(m, "fix_variables"):
            m.fix_variables(instance, dynamic_inputs)
        else:
            pass

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


def solve(instance, parsed_arguments):
    """

    :param instance:
    :param parsed_arguments:
    :return:
    """
    # Get solver and solve
    solver = SolverFactory(parsed_arguments.solver)

    print("Solving...")
    results = solver.solve(instance,
                           tee=parsed_arguments.quiet,
                           keepfiles=parsed_arguments.keepfiles,
                           symbolic_solver_labels=parsed_arguments.symbolic
                           )
    return results


def export_results(problem_directory, horizon, stage, instance,
                   dynamic_inputs, loaded_modules):
    for m in loaded_modules:
        if hasattr(m, "export_results"):
            m.export_results(problem_directory, horizon, stage, instance,
                             dynamic_inputs)
    else:
        pass


def save_objective_function_value(scenario_directory, horizon, stage, instance):
    """
    Save the objective function value.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param instance:
    :return:
    """
    with open(os.path.join(
            scenario_directory, horizon, stage, "results",
            "objective_function_value.txt"),
            "w") as objective_file:
        objective_file.write(
            "Objective function: " + str(instance.Total_Cost())
        )


def save_duals(scenario_directory, horizon, stage, instance, loaded_modules):
    """
    Save the duals of various constraints.
    :param scenario_directory:
    :param horizon:
    :param stage:
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
            scenario_directory, horizon, stage, "results", str(c) + ".csv"),
            "wb"))
        duals_writer.writerow(instance.constraint_indices[c])
        for index in constraint_object:
            duals_writer.writerow(list(index) +
                            [instance.dual[constraint_object[index]]])


def run_scenario(structure, parsed_arguments):
    """
    Check if there are scenario subproblems and solve each problem
    :param structure:
    :param parsed_arguments:
    :return:
    """
    # If no horizon subproblems (empty list), run main problem
    if not structure.horizon_subproblems:
        run_optimization(structure.main_scenario_directory, "", "",
                         parsed_arguments)
    else:
        for h in structure.horizon_subproblems:
            # If no stage subproblems (empty list), run horizon problem
            if not structure.stage_subproblems[h]:
                print("Running horizon {}".format(h))
                run_optimization(
                    structure.main_scenario_directory, h, "",
                    parsed_arguments)
            else:
                for s in structure.stage_subproblems[h]:
                    print("Running horizon {}, stage {}".format(h, s))
                    run_optimization(
                        structure.main_scenario_directory,
                        h, s, parsed_arguments)


# Auxiliary functions
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


# Parse run options
def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument("--scenario",
                        help="Name of the scenario problem to solve.")
    parser.add_argument("--scenario_location", default="runs",
                        help="Name of the scenario problem to solve.")

    # Solve options
    parser.add_argument("--solver", default="cbc",
                        help="Name of the solver to use. Default is cbc.")
    parser.add_argument("--quiet", default=True, action="store_false",
                        help="Don't print solver output if set to true.")
    parser.add_argument("--keepfiles", default=False, action="store_true",
                        help="Save temporary solver files in logs directory.")
    parser.add_argument("--symbolic", default=False, action="store_true",
                        help="Use symbolic labels in solver files.")

    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


if __name__ == "__main__":
    # Get arguments
    args = sys.argv[1:]
    # Parse arguments
    parsed_args = parse_arguments(args)
    # Figure out the scenario structure (i.e. horizons and stages)
    scenario_structure = ScenarioStructure(parsed_args.scenario,
                                           parsed_args.scenario_location)
    # Run the optimization
    run_scenario(scenario_structure, parsed_args)
