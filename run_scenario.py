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
# from pyomo.util.infeasible import log_infeasible_constraints
from pyutilib.services import TempfileManager
import sys
import traceback

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

        # Check if the scenario actually exists
        if not os.path.exists(self.main_scenario_directory):
            raise IOError("Scenario '{}/{}' does not exist. Please verify"
                          " scenario name and scenario location"
                          .format(scenario_location, scenario))

        # Check if there are horizon subproblems
        # If yes, make list of horizon subproblem names and
        # make a dictionary with the horizon subproblem name as key and
        # the horizon subproblem directory as value
        if self.check_for_subproblems(self.main_scenario_directory):
            self.horizons_flag = True
            self.horizon_subproblems = \
                self.get_subproblems(self.main_scenario_directory)
            self.horizon_subproblem_directories = \
                {h: os.path.join(self.main_scenario_directory, h)
                 for h in self.horizon_subproblems}

            # For each horizon subproblem, check if there are stage subproblems
            self.stage_subproblems = {}
            self.stage_subproblem_directories = {}
            for h in self.horizon_subproblems:
                # If there are stage subproblems, make dictionaries of stages
                # by horizon and of stage directories by horizon and stage
                if self.check_for_subproblems(
                        self.horizon_subproblem_directories[h]):
                    self.stages_flag = True
                    self.stage_subproblems[h] = \
                        self.get_subproblems(
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
                            ["project", "timepoint", "stage",
                             "final_commitment_stage", "commitment"])

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

    # Auxiliary functions
    @staticmethod
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

    @staticmethod
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
                """ERROR! Subproblems file {} not found""".
                format(subproblems_file)
            )
            traceback.print_exc()
            sys.exit(1)


def create_and_solve_problem(scenario_directory, subproblem, stage,
                             parsed_arguments):
    """
    :param scenario_directory: the main scenario directory
    :param subproblem: the horizon subproblem name
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
                                scenario_directory, subproblem, stage)

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
                                       scenario_directory, subproblem, stage)

    # Build the problem instance; this will also call any BuildActions that
    # construct the dynamic inputs
    # TODO: pretty sure there aren't any BuildActions left (?)
    if not parsed_arguments.quiet:
        print("Creating problem instance...")
    instance = create_problem_instance(model, scenario_data)

    # Fix variables if modules request so
    instance = fix_variables(instance, dynamic_components, loaded_modules)

    # Solve
    if not parsed_arguments.quiet:
        print("Solving...")
    solve(instance, parsed_arguments)

    return modules_to_use, loaded_modules, dynamic_components, instance


def run_optimization(scenario_directory, subproblem, stage, parsed_arguments):
    """
    :param scenario_directory: the main scenario directory
    :param subproblem: if there are horizon subproblems, the horizon
    :param stage: if there are stage subproblems, the stage
    :param parsed_arguments: the parsed script arguments
    :return: return the objective function value (Total_Cost); only used in
    testing

    Log each run in the (sub)problem directory if requested by the user.

    Create and solve the (sub)problem. See *create_and_solve_problem* method.

    Save results. See *save_results* method.

    Summarize results. See *summarize_results* method.

    Return the objective function (Total_Cost) value; only used in testing mode

    """

    # If directed to do so, log optimization run
    if parsed_arguments.log:
        logs_directory = create_logs_directory_if_not_exists(
            scenario_directory, subproblem, stage)

        # Save sys.stdout so we can return to it later
        stdout_original = sys.stdout

        # The print statement will call the write() method of any object
        # you assign to sys.stdout (in this case the Logging object). The
        # write method of Logging writes both to sys.stdout and a log file
        # (see auxiliary/auxiliary.py)
        sys.stdout = Logging(logs_dir=logs_directory)

    # If directed, set temporary file directory to be the logs directory
    # In conjunction with --keepfiles, this will write the solver solution
    # files into the log directory (rather than a hidden temp folder).
    # Use the --symbolic argument as well for best debugging results
    if parsed_arguments.write_solver_files_to_logs_dir:
        logs_directory = create_logs_directory_if_not_exists(
            scenario_directory, subproblem, stage)
        TempfileManager.tempdir = logs_directory

    if not parsed_arguments.quiet:
        print("\nRunning optimization for scenario {}"
              .format(scenario_directory.split("/")[-1]))
        if subproblem != "":
            print("--- subproblem {}".format(subproblem))
        if stage != "":
            print("--- stage {}".format(stage))

    # Create problem instance and solve it
    modules_to_use, loaded_modules, dynamic_components, instance = \
        create_and_solve_problem(scenario_directory, subproblem, stage,
                                 parsed_arguments)

    # Save the scenario results to disk
    save_results(scenario_directory, subproblem, stage, loaded_modules,
                 dynamic_components, instance, parsed_arguments)

    # Summarize results
    summarize_results(scenario_directory, subproblem, stage, loaded_modules,
                      dynamic_components, parsed_arguments)

    # If logging, we need to return sys.stdout to original (i.e. stop writing
    # to log file)
    if parsed_arguments.log:
        sys.stdout = stdout_original

    # Return the objective function value (in 'testing' mode,
    # the value gets checked against the expected value)
    return instance.Total_Cost()


def run_scenario(structure, parsed_arguments):
    """
    :param structure: the scenario structure object (i.e. horizon and stage
        subproblems)
    :param parsed_arguments:
    :return: the objective function value (Total_Cost); only used in
     'testing' mode.

    Check the scenario structure, iterate over all subproblems if they
    exist, and run the subproblem optimization.

    The objective function is returned, but it's only really used if we
    are in 'testing' mode.
    """
    # If no horizon subproblems (empty list), run main problem
    if not structure.horizon_subproblems:
        objective_values = run_optimization(
            structure.main_scenario_directory, "", "", parsed_arguments)
    else:
        # Create dictionary with which we'll keep track
        # of subproblem objective function values
        objective_values = {}
        for h in structure.horizon_subproblems:
            # If no stage subproblems (empty list), run horizon problem
            if not structure.stage_subproblems[h]:
                objective_values[h] = run_optimization(
                    structure.main_scenario_directory, h, "",
                    parsed_arguments)
            else:
                objective_values[h] = {}
                for s in structure.stage_subproblems[h]:
                    objective_values[h][s] = \
                        run_optimization(
                            structure.main_scenario_directory, h, s,
                            parsed_arguments)
    return objective_values


def save_results(scenario_directory, subproblem, stage, loaded_modules,
                 dynamic_components, instance, parsed_arguments):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param loaded_modules:
    :param dynamic_components:
    :param instance: model instance (solution loaded after solving by default)
    :param parsed_arguments:
    :return:

    Create a results directory for the (sub)problem.
    Export results.
    Export pass through imports.
    Save objective function value.
    Save constraint duals.
    """
    if not parsed_arguments.quiet:
        print("Saving results...")

    # TODO: how best to handle non-empty results directories?
    results_directory = os.path.join(scenario_directory, subproblem, stage,
                                     "results")
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    export_results(scenario_directory, subproblem, stage, instance,
                   dynamic_components, loaded_modules)

    export_pass_through_inputs(scenario_directory, subproblem, stage, instance,
                               dynamic_components, loaded_modules)

    save_objective_function_value(scenario_directory, subproblem, stage, instance)

    save_duals(scenario_directory, subproblem, stage, instance, loaded_modules)


def populate_dynamic_components(dynamic_components, loaded_modules,
                                scenario_directory, subproblem, stage):
    """
    :param dynamic_components: the dynamic components class we're populating
    :param loaded_modules: list of the needed imported modules (Python objects)
    :param scenario_directory: the main scenario directory
    :param subproblem: the horizon subproblem name
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
                                           scenario_directory, subproblem, stage)
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
                       scenario_directory, subproblem, stage):
    """
    :param model: the Pyomo abstract model object with components added
    :param dynamic_components: the dynamic components class
    :param loaded_modules: list of the imported GridPath modules as Python
        objects
    :param scenario_directory: the main scenario directory
    :param subproblem: the horizon subproblem
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
                              scenario_directory, subproblem, stage)
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
    :param loaded_modules:
    :param instance:
    :return:

    View data (for debugging)
    """
    for m in loaded_modules:
        if hasattr(m, "view_loaded_data"):
            m.view_loaded_data(instance)


def solve(instance, parsed_arguments):
    """
    :param instance: the compiled problem instance
    :param parsed_arguments: the user-defined arguments (parsed)
    :return: the problem results

    Send the compiled problem instance to the solver and solve.
    """
    # Get solver
    solver = SolverFactory(parsed_arguments.solver)

    # Solve
    # Note: Pyomo moves the results to the instance object by default.
    # If you want the results to stay into a results object, set the
    # load_solutions argument to False:
    # >>> results = solver.solve(instance, load_solutions=False)

    solver.solve(
        instance,
        tee=not parsed_arguments.mute_solver_output,
        keepfiles=parsed_arguments.keepfiles,
        symbolic_solver_labels=parsed_arguments.symbolic
    )

    # Can optionally log infeasibilities but this has resulted in false
    # positives due to rounding errors larger than the default tolerance
    # of 1E-6.
    # log_infeasible_constraints(instance)


def create_logs_directory_if_not_exists(scenario_directory, subproblem, stage):
    """
    Create a logs directory if it doesn't exist already
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    logs_directory = os.path.join(scenario_directory, subproblem, stage, "logs")
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
    return logs_directory

#
# def log_run(scenario_directory, subproblem, stage, parsed_arguments):
#     """
#     :param scenario_directory:
#     :param subproblem:
#     :param stage:
#     :param parsed_arguments:
#     :return:
#
#     Log run output to a logs file and/or write temporary files in logs dir
#     """
#     logs_directory = os.path.join(scenario_directory, subproblem, stage,
#                                   "logs")
#
#     if (not os.path.exists(logs_directory)) and \
#             (parsed_arguments.write_solver_files_to_logs_dir or
#              parsed_arguments.log):
#         os.makedirs(logs_directory)
#
#     # Set temporary file directory to be the logs directory
#     # In conjunction with --keepfiles, this will write the solver solution
#     # files into the log directory (rather than a hidden temp folder).
#     # Use the --symbolic argument as well for best debugging results
#     if parsed_arguments.write_solver_files_to_logs_dir:
#         TempfileManager.tempdir = logs_directory
#     else:
#         pass
#
#     # Log output to assigned destinations (terminal and a log file in the
#     # logs directory) if directed to do so
#     if parsed_arguments.log:
#         sys.stdout = Logging(logs_dir=logs_directory)
#         # The print statement will call the write() method of any object
#         # you assign to sys.stdout (in this case the Logging object). The
#         # write method of Logging writes both to sys.stdout and a log file
#         # see auxiliary/axiliary.py
#     else:
#         pass


def export_results(scenario_directory, subproblem, stage, instance,
                   dynamic_components, loaded_modules):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance:
    :param dynamic_components:
    :param loaded_modules:
    :return:

    Export results for each loaded module (if applicable)
    """
    for m in loaded_modules:
        if hasattr(m, "export_results"):
            m.export_results(scenario_directory, subproblem, stage, instance,
                             dynamic_components)
    else:
        pass


def export_pass_through_inputs(scenario_directory, subproblem, stage, instance,
                               dynamic_components, loaded_modules):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance:
    :param dynamic_components:
    :param loaded_modules:
    :return:

    Export pass through inputs for each loaded module (if applicable)
    """
    for m in loaded_modules:
        if hasattr(m, "export_pass_through_inputs"):
            m.export_pass_through_inputs(
                scenario_directory, subproblem, stage,
                instance, dynamic_components
            )
    else:
        pass


def save_objective_function_value(scenario_directory, subproblem, stage,
                                  instance):
    """
    Save the objective function value.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance:
    :return:
    """
    objective_function_value = instance.Total_Cost()

    # Round objective function value of test examples
    if os.path.dirname(scenario_directory)[-8:] == 'examples':
        objective_function_value = round(objective_function_value, 2)

    with open(os.path.join(
            scenario_directory, subproblem, stage, "results",
            "objective_function_value.txt"),
            "w") as objective_file:
        objective_file.write(
            "Objective function: " + str(objective_function_value)
        )


def save_duals(scenario_directory, subproblem, stage, instance, loaded_modules):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance:
    :param loaded_modules:
    :return:

    Save the duals of various constraints.
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
            scenario_directory, subproblem, stage, "results", str(c) + ".csv"),
            "w"
        ) as duals_results_file:
            duals_writer = writer(duals_results_file)
            duals_writer.writerow(instance.constraint_indices[c])
            for index in constraint_object:
                duals_writer.writerow(list(index) +
                                      [instance.dual[constraint_object[index]]]
                                      )


def summarize_results(scenario_directory, subproblem, stage, loaded_modules,
                      dynamic_components, parsed_arguments):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param loaded_modules:
    :param dynamic_components:
    :param parsed_arguments:
    :return:

    Summarize results (after results export)
    """
    if not parsed_arguments.quiet:
        print("Summarizing results...")

    # Make the summary results file
    summary_results_file = os.path.join(
        scenario_directory, subproblem, stage, "results", "summary_results.txt"
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
            m.summarize_results(dynamic_components, scenario_directory, subproblem,
                                stage)
    else:
        pass


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
    parser.add_argument("--mute_solver_output", default=False,
                        action="store_true",
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
                        help="Flag for test suite runs.")

    # Flag for updating run status in the database
    parser.add_argument("--update_db_run_status", default=False,
                        action="store_true",
                        help="Flag for updating run status in the database.")

    # Parse arguments
    parsed_arguments = parser.parse_args(args=arguments)

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

    # Run the scenario (can be multiple optimization subproblems)
    expected_objective_values = run_scenario(
        scenario_structure, parsed_args)

    # Return the objective function values (used in testing)
    return expected_objective_values


if __name__ == "__main__":
    main()
