#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This script runs a GridPath scenario. It assumes that scenario inputs have
already been written.
"""
from __future__ import print_function

from builtins import str
from builtins import object
from argparse import ArgumentParser
from csv import writer
import os.path
import pandas as pd
from pyomo.environ import AbstractModel, Suffix, DataPortal, SolverFactory
from pyutilib.services import TempfileManager
import sys

from gridpath.auxiliary.auxiliary import Logging
from gridpath.auxiliary.dynamic_components import DynamicComponents
from gridpath.auxiliary.module_list import determine_modules, load_modules


class ScenarioStructure(object):
    """
    This class defines the scenario structure, i.e. is the scenario a single
    problem or does it consist of subproblems, both horizon subproblems and
    stage subproblems for each horizon.

    Based on the subproblem structure, we will define the directory and file
    structure for the scenario including where the inputs and outputs are
    written, and where to write any pass-through inputs.

    The scenario structure will then be passed to other methods that iterate
    over and solve each subproblem.
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
                # If there are stage subproblems, make dictionaries of stages
                # by horizon and of stage directories by horizon and stage
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
                    # First create the pass-through directory if it doesn't
                    # exist
                    # TODO: need better handling of deleting prior results?
                    pass_through_directory = \
                        os.path.join(
                            self.horizon_subproblem_directories[h],
                            "pass_through_inputs")
                    if not os.path.exists(pass_through_directory):
                        os.makedirs(pass_through_directory)
                    with open(
                            os.path.join(
                                pass_through_directory,
                                "fixed_commitment.tab"
                            ), "w"
                    ) as fixed_commitment_file:
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


def create_and_solve_problem(scenario_directory, horizon, stage,
                             parsed_arguments):
    """
    :param scenario_directory: the main scenario directory
    :param horizon: the horizon subproblem name
    :param stage: the stage subproblem name
    :param parsed_arguments: the user-defined script arguments
    :return: modules_to_use (list of module names used in scenario),
        loaded_modules (Python objects), dynamic_inputs (the populated
        dynamic components class), instance (the problem instance), results
        (the optimization results)

    This method creates the problem instance and solves it.

    To create the problem, we use a Pyomo AbstractModel() class. We will add
    Pyomo optimization components to this class, will load data into the
    components, and will then compile the problem.

    We first need to determine which GridPath modules we need to use. See
    *determine_modules* method (imported from
    *gridpath.auxiilary.module_list*) and import those modules (via the
    *load_modules* method imported from *gridpath.auxiliary.module_list*).

    We then determine the dynamic model components based on the selected
    modules and input data. See *populate_dynamic_components* method.

    The next step is to create the abstract model (see *create_abstract_model*
    method) and load the input data into its components (see
    *load_scenario_data*).

    Finally, we compile and solve the problem (*create_problem_instance* and
    *solve* methods respectively). If any variables need to be fixed,
    this is done before solving (see the *fix_variables* method).
    """
    # Create pyomo abstract model class
    model = AbstractModel()

    # Determine and load modules
    modules_to_use = determine_modules(scenario_directory)
    loaded_modules = load_modules(modules_to_use)

    # Initialize the dynamic components class
    dynamic_components = DynamicComponents()

    # Determine the dynamic components based on the needed modules and input
    # data
    populate_dynamic_components(dynamic_components, loaded_modules,
                                scenario_directory, horizon, stage)

    # Create the abstract model; some components are initialized here
    if not parsed_arguments.quiet:
        print("Building model...")
    create_abstract_model(model, dynamic_components, loaded_modules)

    # Create a dual suffix component
    # TODO: maybe this shouldn't always be needed
    model.dual = Suffix(direction=Suffix.IMPORT)

    # Load the scenario data
    if not parsed_arguments.quiet:
        print("Loading data...")
    scenario_data = load_scenario_data(model, dynamic_components, loaded_modules,
                                       scenario_directory, horizon, stage)

    # Build the problem instance; this will also call any BuildActions that
    # construct the dynamic inputs
    # TODO: pretty sure there aren't any BuildActions left (?)
    if not parsed_arguments.quiet:
        print("Creating problem instance...")
    instance = create_problem_instance(model, scenario_data)

    # Fix variables if modules request so
    instance = fix_variables(instance, dynamic_components, loaded_modules)

    # Solve
    results = solve(instance, parsed_arguments)

    return modules_to_use, loaded_modules, dynamic_components, instance, results


def run_optimization(scenario_directory, horizon, stage, parsed_arguments):
    """
    :param scenario_directory: the main scenario directory
    :param horizon: if there are horizon subproblems, the horizon
    :param stage: if there are stage subproblems, the stage
    :param parsed_arguments: the parsed script arguments
    :return: return the objective function value (Total_Cost); only used in
    testing

    Create a results directory for the subproblem.

    Create and solve the subproblem. See *create_and_solve_problem* method.

    If applicable (i.e. a loaded module requires it), export any pass-through
    inputs. See *export_pass_through_inputs* method.

    Save results. See *save_results* method.

    Summarize results. See *summarize_results* method.

    Return the objective function (Total_Cost) value; only used in testing mode
    """

    # TODO: how best to handle non-empty results directories?
    # Make results and logs directories
    results_directory = os.path.join(scenario_directory, horizon, stage,
                                     "results")
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    modules_to_use, loaded_modules, dynamic_components, instance, results = \
        create_and_solve_problem(scenario_directory, horizon, stage,
                                 parsed_arguments)

    # Export pass-through results if modules require it
    export_pass_through_inputs(scenario_directory, horizon, stage, instance,
                               dynamic_components, loaded_modules)

    # Save the scenario results to disk
    save_results(scenario_directory, horizon, stage, loaded_modules,
                 dynamic_components, instance, results, parsed_arguments)

    # Summarize results
    summarize_results(scenario_directory, horizon, stage, loaded_modules,
                      dynamic_components, parsed_arguments)

    # Return the objective function value
    # In 'testing' mode, this gets checked against expected value
    return round(instance.Total_Cost(), 2)


def save_results(scenario_directory, horizon, stage, loaded_modules,
                 dynamic_components, instance, results, parsed_arguments):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param loaded_modules:
    :param dynamic_components:
    :param instance:
    :param results:
    :param parsed_arguments:
    :return:
    """
    # RESULTS
    instance.solutions.load_from(results)

    save_objective_function_value(scenario_directory, horizon, stage, instance)

    save_duals(scenario_directory, horizon, stage, instance, loaded_modules)

    export_results(scenario_directory, horizon, stage, instance,
                   dynamic_components, loaded_modules, parsed_arguments)


def populate_dynamic_components(dynamic_components, loaded_modules,
                                scenario_directory, horizon, stage):
    """
    :param dynamic_components: the dynamic components class we're populating
    :param loaded_modules: list of the needed imported modules (Python objects)
    :param scenario_directory: the main scenario directory
    :param horizon: the horizon subproblem name
    :param stage: the stage subproblem name

    We iterate over all required modules and call their
    *determine_dynamic_components* method, if applicable, in order to add
    the dynamic components to the *dynamic_components* class object,
    which we will then pass to the *add_model_components* module methods,
    so that the applicable components can be added to the abstract model.
    """
    for m in loaded_modules:
        if hasattr(m, 'determine_dynamic_components'):
            m.determine_dynamic_components(dynamic_components,
                                           scenario_directory, horizon, stage)
        else:
            pass


def create_abstract_model(model, dynamic_components, loaded_modules):
    """
    :param model: the Pyomo AbstractModel object
    :param dynamic_components: the populated dynamic model components class
    :param loaded_modules: list of the required modules as Python objects

    To create the abstract model, we iterate over all required modules and
    call their *add_model_components* method to add components to the Pyomo
    AbstractModel. Some modules' *add_model_components* method also require the
    dynamic component class as an argument for any dynamic components to be
    added to the model.
    """
    for m in loaded_modules:
        if hasattr(m, 'add_model_components'):
            m.add_model_components(model, dynamic_components)


def load_scenario_data(model, dynamic_components, loaded_modules,
                       scenario_directory, horizon, stage):
    """
    :param model: the Pyomo abstract model object with components added
    :param dynamic_components: the dynamic components class
    :param loaded_modules: list of the imported GridPath modules as Python
        objects
    :param scenario_directory: the main scenario directory
    :param horizon: the horizon subproblem
    :param stage: the stage subproblem
    :return: the DataPortal object populated with the input data

    Iterate over all required GridPath modules and call their
    *load_model_data* method in order to load input data into the relevant
    model components. Return the resulting DataPortal object with the data
    loaded in.
    """
    # Load data
    data_portal = DataPortal()
    for m in loaded_modules:
        if hasattr(m, "load_model_data"):
            m.load_model_data(model, dynamic_components, data_portal,
                              scenario_directory, horizon, stage)
        else:
            pass
    return data_portal


def create_problem_instance(model, loaded_data):
    """
    :param model: the AbstractModel Pyomo object with components added
    :param loaded_data: the DataPortal object with the data loaded in and
        linked to the relevant model components
    :return: the compiled problem instance

    Compile the problem based on the abstract model formulation and the data
    loaded into the model components.
    """
    # Create problem instance
    instance = model.create_instance(loaded_data)
    return instance


def fix_variables(instance, dynamic_components, loaded_modules):
    """
    :param instance: the compiled problem instance
    :param dynamic_components: the dynamic component class
    :param loaded_modules: list of imported GridPath modules as Python objects
    :return: the problem instance with the relevant variables fixed

    Iterate over the required GridPath modules and fix variables by calling
    the modules' *fix_variables*, if applicable. Return the modified
    problem instance with the relevant variables fixed.
    """
    for m in loaded_modules:
        if hasattr(m, "fix_variables"):
            m.fix_variables(instance, dynamic_components)
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
    :param instance: the compiled problem instance
    :param parsed_arguments: the user-defined arguments (parsed)
    :return: the problem results

    Send the compiled problem instance to the solver and solve. Return the
    results (solver output).
    """
    # Get solver and solve
    solver = SolverFactory(parsed_arguments.solver)

    if not parsed_arguments.quiet:
        print("Solving...")
    results = solver.solve(
        instance,
        tee=parsed_arguments.mute_solver_output,
        keepfiles=parsed_arguments.keepfiles,
        symbolic_solver_labels=parsed_arguments.symbolic
    )
    return results


def log_run(scenario_directory, horizon, stage, parsed_arguments):
    """
    Log run output to a logs file and/or write temporary files in logs dir
    :param scenario_directory: 
    :param horizon: 
    :param stage: 
    :param parsed_arguments: 
    :return: 
    """
    logs_directory = os.path.join(scenario_directory, horizon, stage,
                                  "logs")

    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)

    # Write temporary files to logs directory if directed to do so
    # This can be useful for debugging in conjunction with the --keepfiles
    # and --symbolic arguments
    if parsed_arguments.write_solver_files_to_logs_dir:
        TempfileManager.tempdir = logs_directory
    else:
        pass

    # Log output to assigned destinations (terminal and a log file in the
    # logs directory) if directed to do so
    if parsed_arguments.log:
        sys.stdout = Logging(logs_dir=logs_directory)
    else:
        pass


def export_results(problem_directory, horizon, stage, instance,
                   dynamic_components, loaded_modules, parsed_arguments):
    if not parsed_arguments.quiet:
        print("Exporting results...")
    for m in loaded_modules:
        if hasattr(m, "export_results"):
            m.export_results(problem_directory, horizon, stage, instance,
                             dynamic_components)
    else:
        pass


def export_pass_through_inputs(problem_directory, horizon, stage, instance,
                               dynamic_components, loaded_modules):
    for m in loaded_modules:
        if hasattr(m, "export_pass_through_inputs"):
            m.export_pass_through_inputs(
                problem_directory, horizon, stage, instance, dynamic_components
            )
    else:
        pass


def save_objective_function_value(scenario_directory, horizon, stage, instance
                                  ):
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
            "Objective function: " + str(round(instance.Total_Cost(), 2))
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

    for c in list(instance.constraint_indices.keys()):
        constraint_object = getattr(instance, c)
        with open(os.path.join(
            scenario_directory, horizon, stage, "results", str(c) + ".csv"),
            "w"
        ) as duals_results_file:
            duals_writer = writer(duals_results_file)
            duals_writer.writerow(instance.constraint_indices[c])
            for index in constraint_object:
                duals_writer.writerow(list(index) +
                                      [instance.dual[constraint_object[index]]]
                                      )


def summarize_results(problem_directory, horizon, stage, loaded_modules,
                      dynamic_components, parsed_arguments):
    """
    Summarize results (after results export)
    :param problem_directory:
    :param horizon:
    :param stage:
    :param loaded_modules:
    :param dynamic_components:
    :param parsed_arguments:
    :return:
    """
    if not parsed_arguments.quiet:
        print("Summarizing results...")

    # Make the summary results file
    summary_results_file = os.path.join(
        problem_directory, horizon, stage, "results", "summary_results.txt"
    )

    # TODO: how to handle results from previous runs
    # Overwrite prior results
    with open(summary_results_file, "w") as outfile:
        outfile.write("##### SUMMARY RESULTS FOR SCENARIO *{}* #####\n".format(
            parsed_arguments.scenario)
        )

    # Go through the modules and get the appropriate results
    for m in loaded_modules:
        if hasattr(m, "summarize_results"):
            m.summarize_results(dynamic_components, problem_directory, horizon,
                                stage)
    else:
        pass


def run_scenario(structure, parsed_arguments):
    """
    :param structure: the scenario structure (i.e. horizon and stage
        subproblems)
    :param parsed_arguments:
    :return: the objective function value (Total_Cost); only used in
     'testing' mode.

    Check the scenario structure, iterate over all subproblems if they
    exist, and run the subproblem optimization.

    The objective function is returned, but it's only really used if we
    are in 'testing' mode.

    We also log each run in the subproblem directory if requested by the user.
    """

    # TODO: why is this here? shouldn't this be in dealt with in log_run()?
    # Log output to file if instructed
    stdout_original = sys.stdout  # will return sys.stdout to original

    # If no horizon subproblems (empty list), run main problem
    if not structure.horizon_subproblems:
        log_run(structure.main_scenario_directory, "", "",
                parsed_arguments)
        objective_values = run_optimization(
            structure.main_scenario_directory, "", "", parsed_arguments)
        # Return sys.stdout to original (i.e. stop writing to log file)
        sys.stdout = stdout_original
    else:
        # Create dictionary with which we'll keep track
        # of subproblem objective function values
        objective_values = {}
        for h in structure.horizon_subproblems:
            # If no stage subproblems (empty list), run horizon problem
            if not structure.stage_subproblems[h]:
                log_run(structure.main_scenario_directory, h, "",
                        parsed_arguments)
                if not parsed_arguments.quiet:
                    print("Running horizon {}".format(h))
                objective_values[h] = run_optimization(
                    structure.main_scenario_directory, h, "",
                    parsed_arguments)
                # Return sys.stdout to original (i.e. stop writing to log file)
                sys.stdout = stdout_original
            else:
                objective_values[h] = {}
                for s in structure.stage_subproblems[h]:
                    log_run(structure.main_scenario_directory, h, s,
                            parsed_arguments)
                    if not parsed_arguments.quiet:
                        print("Running horizon {}, stage {}".format(h, s))
                    objective_values[h][s] = \
                        run_optimization(
                            structure.main_scenario_directory, h, s,
                            parsed_arguments)
                    # Return sys.stdout to original
                    # (i.e. stop writing to log file)
                    sys.stdout = stdout_original

    return objective_values


# Auxiliary functions
def check_for_subproblems(directory):
    """
    :param directory: the directory where we're looking for a
        'subproblems.csv' file
    :return: True or False

    Check for subproblems. Currently, this is done by checking if a
    'subproblems.csv' file exists in the directory.

    .. todo:: a subproblems file may not be how we tell GridPath what the
        scenario structure is; we need to think about what the best way to
        do this is, particularly in the context of linking to the database
    """
    subproblems_file = \
        os.path.join(directory, "subproblems.csv")
    if os.path.isfile(subproblems_file):
        return True
    else:
        return False


def get_subproblems(directory):
    """
    :param directory:
    :return: a list of the subproblems

    Get the names of the subproblems from the CSV.
    """
    subproblems_file = os.path.join(directory, "subproblems.csv")
    try:
        subproblems = \
            [str(sp) for sp in pd.read_csv(subproblems_file)["subproblems"]
                .tolist()]
        return subproblems
    except IOError:
        print(
            """ERROR! Subproblems file {} not found""".format(subproblems_file)
        )
        sys.exit(1)


# Parse run options
def parse_arguments(arguments):
    """

    :param arguments: the script arguments specified by the user
    :return: the parsed argument values (<class 'argparse.Namespace'> Python
        object)
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument("--scenario",
                        help="Name of the scenario problem to solve.")
    parser.add_argument("--scenario_location", default="scenarios",
                        help="Scenario directory path (relative to "
                             "run_scenario.py.")

    # Output options
    parser.add_argument("--log", default=False, action="store_true",
                        help="Log output to a file in the logs directory as "
                             "well as the terminal.")
    parser.add_argument("--quiet", default=False, action="store_true",
                        help="Don't print run output.")

    # Solve options
    parser.add_argument("--solver", default="cbc",
                        help="Name of the solver to use. Default is cbc.")
    parser.add_argument("--mute_solver_output", default=True,
                        action="store_false",
                        help="Don't print solver output if set to true.")
    parser.add_argument("--write_solver_files_to_logs_dir", default=False,
                        action="store_true", help="Write the temporary "
                                                  "solver files to the logs "
                                                  "directory.")
    parser.add_argument("--keepfiles", default=False, action="store_true",
                        help="Save temporary solver files.")
    parser.add_argument("--symbolic", default=False, action="store_true",
                        help="Use symbolic labels in solver files.")

    # Flag for test runs (various changes in behavior)
    parser.add_argument("--testing", default=False, action="store_true",
                        help="Flag for test suite runs. Results not saved.")

    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


def main(args=None):
    """
    This is the 'main' method that runs a scenario. It takes in and parses the
    script arguments, determines the scenario structure (i.e. whether it is a
    single optimization or has subproblems), and runs the scenario.
    This method also returns the objective function value(s).
    """

    if args is None:
        args = sys.argv[1:]
    # Parse arguments
    parsed_args = parse_arguments(args)

    # Figure out the scenario structure (i.e. horizons and stages)
    scenario_structure = ScenarioStructure(parsed_args.scenario,
                                           parsed_args.scenario_location)
    # Run the optimization
    expected_objective_values = run_scenario(
        scenario_structure, parsed_args)
    return expected_objective_values


if __name__ == "__main__":
    main()
