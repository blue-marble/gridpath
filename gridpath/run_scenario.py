#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This script runs a GridPath scenario. It assumes that scenario inputs have
already been written.

The main() function of this script can also be called with the
*gridpath_run* command when GridPath is installed.
"""
from __future__ import print_function

from builtins import str
from builtins import object
import argparse
from csv import reader, writer
import datetime
import os.path
from pyomo.environ import AbstractModel, Suffix, DataPortal, SolverFactory
# from pyomo.util.infeasible import log_infeasible_constraints
from pyutilib.services import TempfileManager
import sys

from gridpath.auxiliary.auxiliary import check_for_integer_subdirectories
from gridpath.common_functions import determine_scenario_directory, \
    get_scenario_name_parser, get_required_e2e_arguments_parser, get_solve_parser, \
    create_logs_directory_if_not_exists, Logging
from gridpath.auxiliary.dynamic_components import DynamicComponents
from gridpath.auxiliary.module_list import determine_modules, load_modules


class ScenarioStructure(object):
    """
    This class defines the scenario structure, i.e. is the scenario a single
    problem or does it consist of multiple subproblems, and whether there are
    stages for each subproblem.

    Based on the subproblem structure, we will define the directory and file
    structure for the scenario including where the inputs and outputs are
    written, and where to write any pass-through inputs.

    The scenario structure will then be passed to other methods that iterate
    over and solve each subproblem.
    """
    def __init__(self, scenario, scenario_location):
        self.main_scenario_directory = determine_scenario_directory(
            scenario_location=scenario_location, scenario_name=scenario
        )

        # Check if the scenario actually exists
        if not os.path.exists(self.main_scenario_directory):
            raise IOError("Scenario '{}/{}' does not exist. Please verify"
                          " scenario name and scenario location"
                          .format(scenario_location, scenario))

        # Check if there are subproblem directories
        self.subproblems = \
            check_for_integer_subdirectories(self.main_scenario_directory)

        # Make dictionary for the stages by subproblem, starting with empty
        # list for each subproblem
        self.stages_by_subproblem = {
            subp: [] for subp in self.subproblems
        }

        # If we have subproblems, check for stage subdirectories for each
        # subproblem directory
        if self.subproblems:
            for subproblem in self.subproblems:
                subproblem_dir = os.path.join(
                    self.main_scenario_directory, subproblem
                )
                stages = check_for_integer_subdirectories(subproblem_dir)
                # If the list isn't empty, update the stage dictionary and
                # create the stage pass-through directory and input file
                # TODO: we probably don't need a directory for the
                #  pass-through inputs, as it's only one file
                if stages:
                    self.stages_by_subproblem[subproblem] = stages
                    # Create the commitment pass-through file (also deletes any
                    # prior results)
                    # First create the pass-through directory if it doesn't
                    # exist
                    # TODO: need better handling of deleting prior results?
                    pass_through_directory = \
                        os.path.join(subproblem_dir, "pass_through_inputs")
                    if not os.path.exists(pass_through_directory):
                        os.makedirs(pass_through_directory)
                    with open(
                            os.path.join(
                                pass_through_directory,
                                "fixed_commitment.tab"
                            ), "w", newline=""
                    ) as fixed_commitment_file:
                        fixed_commitment_writer = writer(
                            fixed_commitment_file,
                            delimiter="\t", lineterminator="\n"
                        )
                        fixed_commitment_writer.writerow(
                            ["project", "timepoint", "stage",
                             "final_commitment_stage", "commitment"])


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

    # Determine/load modules and dynamic components
    modules_to_use, loaded_modules, dynamic_components = \
        set_up_gridpath_modules_and_components(
            scenario_directory=scenario_directory,
            subproblem=subproblem, stage=stage
        )

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
    scenario_data = load_scenario_data(
        model, dynamic_components, loaded_modules,
        scenario_directory, subproblem, stage
    )

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

    return instance


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

    Save results. See *save_results()* method.

    Summarize results. See *summarize_results()* method.

    Return the objective function (Total_Cost) value; only used in testing mode

    """

    # If directed to do so, log optimization run
    if parsed_arguments.log:
        logs_directory = create_logs_directory_if_not_exists(
            scenario_directory, subproblem, stage)

        # Save sys.stdout so we can return to it later
        stdout_original = sys.stdout
        stderr_original = sys.stderr

        # The print statement will call the write() method of any object
        # you assign to sys.stdout (in this case the Logging object). The
        # write method of Logging writes both to sys.stdout and a log file
        # (see auxiliary/auxiliary.py)
        logger = Logging(
            logs_dir=logs_directory,
            start_time=datetime.datetime.now(), e2e=False, process_id=None
        )
        sys.stdout = logger
        sys.stderr = logger

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
    solved_instance = \
        create_and_solve_problem(scenario_directory, subproblem, stage,
                                 parsed_arguments)

    # Save the scenario results to disk
    save_results(
        scenario_directory, subproblem, stage, solved_instance,
        parsed_arguments
    )

    # Summarize results
    summarize_results(scenario_directory, subproblem, stage, parsed_arguments)

    # If logging, we need to return sys.stdout to original (i.e. stop writing
    # to log file)
    if parsed_arguments.log:
        sys.stdout = stdout_original
        sys.stderr = stderr_original

    # Return the objective function value (in 'testing' mode,
    # the value gets checked against the expected value)
    return solved_instance.Total_Cost()


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
    # If no subproblem directories (empty list), run main problem
    if not structure.subproblems:
        objective_values = run_optimization(
            structure.main_scenario_directory, "", "", parsed_arguments)
    else:
        # Create dictionary with which we'll keep track
        # of subproblem objective function values
        objective_values = {}
        for subproblem in structure.subproblems:
            # If no stages in this subproblem (empty list), run the subproblem
            if not structure.stages_by_subproblem[subproblem]:
                objective_values[subproblem] = run_optimization(
                    structure.main_scenario_directory, subproblem, "",
                    parsed_arguments)
            # Otherwise, run the stage problem
            else:
                objective_values[subproblem] = {}
                for stage in structure.stages_by_subproblem[subproblem]:
                    objective_values[subproblem][stage] = \
                        run_optimization(
                            structure.main_scenario_directory,
                            subproblem, stage,
                            parsed_arguments)
    return objective_values


def save_results(scenario_directory, subproblem, stage,
                 instance, parsed_arguments):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
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

    export_results(scenario_directory, subproblem, stage, instance)

    export_pass_through_inputs(scenario_directory, subproblem, stage, instance)

    save_objective_function_value(
        scenario_directory, subproblem, stage, instance
    )

    save_duals(scenario_directory, subproblem, stage, instance)


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
    # Start with solver name specified on command line
    solver_name = parsed_arguments.solver

    # Get any user-requested solver options
    scenario_directory = determine_scenario_directory(
        scenario_location=parsed_arguments.scenario_location,
        scenario_name=parsed_arguments.scenario
    )
    solver_options = dict()
    solver_options_file = os.path.join(scenario_directory,
                                       "solver_options.csv")
    if os.path.exists(solver_options_file):
        with open(solver_options_file) as f:
            _reader = reader(f, delimiter=",")
            for row in _reader:
                solver_options[row[0]] = row[1]

        # Check the the solver specified is the same as that given from the
        # command line (if any)
        if parsed_arguments.solver is not None:
            if parsed_arguments.solver == solver_options["solver"]:
                pass
            else:
                raise UserWarning(
                    "ERROR! Solver specified on command line ({}) and solver "
                    "in solver_options.csv ({}) do not match.".format(
                        parsed_arguments.solver, solver_options["solver"]
                    ))

        # If we make it here, set the solver name from the
        # solver_options.csv file
        solver_name = solver_options["solver"]
    else:
        if parsed_arguments.solver is None:
            solver_name = "cbc"

    # Get solver
    # If a solver executable is specified, pass it to Pyomo
    if parsed_arguments.solver_executable is not None:
        solver = SolverFactory(solver_name,
                               executable=parsed_arguments.solver_executable)
    # Otherwise, only pass the solver name; Pyomo will look for the
    # executable in the PATH
    else:
        solver = SolverFactory(solver_name)

    # Apply the solver options (if any)
    for opt in solver_options.keys():
        if opt == "solver":
            pass  # this is just the solver name, not actually an 'option'
        else:
            solver.options[opt] = solver_options[opt]

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


def export_results(scenario_directory, subproblem, stage, instance):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance:
    :return:

    Export results for each loaded module (if applicable)
    """
    # Determine/load modules and dynamic components
    modules_to_use, loaded_modules, dynamic_components = \
        set_up_gridpath_modules_and_components(
            scenario_directory=scenario_directory,
            subproblem=subproblem, stage=stage
        )

    for m in loaded_modules:
        if hasattr(m, "export_results"):
            m.export_results(scenario_directory, subproblem, stage, instance,
                             dynamic_components)
    else:
        pass


def export_pass_through_inputs(
        scenario_directory, subproblem, stage, instance
):
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
    # Determine/load modules and dynamic components
    modules_to_use, loaded_modules, dynamic_components = \
        set_up_gridpath_modules_and_components(
            scenario_directory=scenario_directory,
            subproblem=subproblem, stage=stage
        )

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
            "w", newline="") as objective_file:
        objective_file.write(
            "Objective function: " + str(objective_function_value)
        )


def save_duals(scenario_directory, subproblem, stage, instance):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance:
    :return:

    Save the duals of various constraints.
    """
    # Determine/load modules and dynamic components
    modules_to_use, loaded_modules, dynamic_components = \
        set_up_gridpath_modules_and_components(
            scenario_directory=scenario_directory,
            subproblem=subproblem, stage=stage
        )

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
            "w", newline=""
        ) as duals_results_file:
            duals_writer = writer(duals_results_file)
            duals_writer.writerow(instance.constraint_indices[c])
            for index in constraint_object:
                duals_writer.writerow(list(index) +
                                      [instance.dual[constraint_object[index]]]
                                      )


def summarize_results(scenario_directory, subproblem, stage, parsed_arguments):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param parsed_arguments:
    :return:

    Summarize results (after results export)
    """
    if not parsed_arguments.quiet:
        print("Summarizing results...")

    # Determine/load modules and dynamic components
    modules_to_use, loaded_modules, dynamic_components = \
        set_up_gridpath_modules_and_components(
            scenario_directory=scenario_directory,
            subproblem=subproblem, stage=stage
        )

    # Make the summary results file
    summary_results_file = os.path.join(
        scenario_directory, subproblem, stage, "results", "summary_results.txt"
    )

    # TODO: how to handle results from previous runs
    # Overwrite prior results
    with open(summary_results_file, "w", newline="") as outfile:
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


def set_up_gridpath_modules_and_components(scenario_directory, subproblem, stage):
    """
    :return: list of the names of the modules the scenario uses, list of the
        loaded modules, and the populated dynamic components for the scenario

    Set up the modules and dynamic components for a scenario run problem
    instance.
    """
    # Determine and load modules
    modules_to_use = determine_modules(scenario_directory=scenario_directory)
    loaded_modules = load_modules(modules_to_use)
    # Determine the dynamic components based on the needed modules and input
    # data
    dynamic_components = DynamicComponents()
    populate_dynamic_components(dynamic_components, loaded_modules,
                                scenario_directory, subproblem, stage)

    return modules_to_use, loaded_modules, dynamic_components


# Parse run options
def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = argparse.ArgumentParser(
        add_help=True,
        parents=[get_scenario_name_parser(), get_required_e2e_arguments_parser(),
                 get_solve_parser()]
    )

    # Flip order of argument groups so "required arguments" show first
    # https://stackoverflow.com/questions/39047075/reorder-python-argparse-argument-groups
    # Note: hacky fix; preferred answer of creating an explicit optional group
    # doesn't work because we combine parsers here with the parents keyword
    parser._action_groups.reverse()

    # Parse arguments
    # TODO: should we throw warning for unknown arguments (here and in the
    #  other scripts)? run_start_to_end does pass unknown arguments (e.g.
    #  the database file path), so we'd have to suppress warnings then
    parsed_arguments = parser.parse_known_args(args=args)[0]

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
