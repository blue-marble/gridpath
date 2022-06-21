# Copyright 2016-2020 Blue Marble Analytics LLC.
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
This script runs a GridPath scenario. It assumes that scenario inputs have
already been written.

The main() function of this script can also be called with the
*gridpath_run* command when GridPath is installed.
"""

import argparse
from csv import reader, writer
import datetime
from multiprocessing import get_context, Manager
import os.path
from pyomo.environ import (
    AbstractModel,
    Suffix,
    DataPortal,
    SolverFactory,
    SolverStatus,
    TerminationCondition,
)

# from pyomo.util.infeasible import log_infeasible_constraints
from pyomo.common.tempfiles import TempfileManager
import sys
import warnings

from gridpath.auxiliary.import_export_rules import import_export_rules
from gridpath.auxiliary.scenario_chars import get_subproblem_structure_from_disk
from gridpath.common_functions import (
    determine_scenario_directory,
    get_scenario_name_parser,
    get_required_e2e_arguments_parser,
    get_run_scenario_parser,
    create_logs_directory_if_not_exists,
    Logging,
)
from gridpath.auxiliary.dynamic_components import DynamicComponents
from gridpath.auxiliary.module_list import determine_modules, load_modules


def create_and_solve_problem(scenario_directory, subproblem, stage, parsed_arguments):
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
    dynamic_components = DynamicComponents()

    # Determine/load modules and dynamic components
    modules_to_use, loaded_modules = set_up_gridpath_modules(
        scenario_directory=scenario_directory, subproblem=subproblem, stage=stage
    )

    # Create the abstract model; some components are initialized here
    if not parsed_arguments.quiet:
        print("Building model...")
    create_abstract_model(
        model, dynamic_components, loaded_modules, scenario_directory, subproblem, stage
    )

    # Create a dual suffix component
    # TODO: maybe this shouldn't always be needed
    model.dual = Suffix(direction=Suffix.IMPORT)

    # Load the scenario data
    if not parsed_arguments.quiet:
        print("Loading data...")
    scenario_data = load_scenario_data(
        model, dynamic_components, loaded_modules, scenario_directory, subproblem, stage
    )

    if not parsed_arguments.quiet:
        print("Creating problem instance...")
    instance = create_problem_instance(model, scenario_data)

    # Fix variables if modules request so
    instance = fix_variables(
        instance,
        dynamic_components,
        scenario_directory,
        subproblem,
        stage,
        loaded_modules,
    )

    # Solve
    if not parsed_arguments.quiet:
        print("Solving...")
    results = solve(instance, parsed_arguments)

    return instance, results, dynamic_components


def run_optimization_for_subproblem_stage(
    scenario_directory,
    subproblem_directory,
    stage_directory,
    parsed_arguments,
):
    """
    :param scenario_directory: the main scenario directory
    :param subproblem_directory: if there are horizon subproblems, the horizon
    :param stage_directory: if there are stage subproblems, the stage
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
            scenario_directory, subproblem_directory, stage_directory
        )

        # Save sys.stdout so we can return to it later
        stdout_original = sys.stdout
        stderr_original = sys.stderr

        # The print statement will call the write() method of any object
        # you assign to sys.stdout (in this case the Logging object). The
        # write method of Logging writes both to sys.stdout and a log file
        # (see auxiliary/auxiliary.py)
        logger = Logging(
            logs_dir=logs_directory,
            start_time=datetime.datetime.now(),
            e2e=False,
            process_id=None,
        )
        sys.stdout = logger
        sys.stderr = logger

    # If directed, set temporary file directory to be the logs directory
    # In conjunction with --keepfiles, this will write the solver solution
    # files into the log directory (rather than a hidden temp folder).
    # Use the --symbolic argument as well for best debugging results
    if parsed_arguments.write_solver_files_to_logs_dir:
        logs_directory = create_logs_directory_if_not_exists(
            scenario_directory, subproblem_directory, stage_directory
        )
        TempfileManager.tempdir = logs_directory

    if not parsed_arguments.quiet:
        print(
            "\nRunning optimization for scenario {}".format(
                scenario_directory.split("/")[-1]
            )
        )
        if subproblem_directory != "":
            print("--- subproblem {}".format(subproblem_directory))
        if stage_directory != "":
            print("--- stage {}".format(stage_directory))

    # We're expecting subproblem and stage to be strings downstream from here
    subproblem_directory = str(subproblem_directory)
    stage_directory = str(stage_directory)

    # Create problem instance and solve it
    solved_instance, results, dynamic_components = create_and_solve_problem(
        scenario_directory, subproblem_directory, stage_directory, parsed_arguments
    )

    # Save the scenario results to disk
    save_results(
        scenario_directory,
        subproblem_directory,
        stage_directory,
        solved_instance,
        results,
        dynamic_components,
        parsed_arguments,
    )

    # Summarize results
    summarize_results(
        scenario_directory,
        subproblem_directory,
        stage_directory,
        parsed_arguments,
    )

    # If logging, we need to return sys.stdout to original (i.e. stop writing
    # to log file)
    if parsed_arguments.log:
        sys.stdout = stdout_original
        sys.stderr = stderr_original

    # Return the objective function value (in the testing suite, the value
    # gets checked against the expected value, but this is the only place
    # this is actually used)
    # TODO: this will need to have a variable for the name of the objective
    #  function component once there are multiple possible objective functions
    if results.solver.termination_condition != "infeasible":
        return solved_instance.NPV()
    else:
        warnings.warn("WARNING: the problem was infeasible!")


def run_optimization_for_subproblem(
    scenario_directory,
    subproblem_structure,
    subproblem,
    parsed_arguments,
    objective_values,
):
    """
    Check if there are stages in the subproblem; if not solve subproblem;
    if, yes, solve each stage sequentially
    """

    # If we only have a single subproblem AND it does not have stages, set the
    # subproblem_string to an empty string (the subproblem directory should not
    # have been created)
    # If we have multiple subproblems or a single subproblems with stages,
    # we're expecting a subproblem directory
    if list(subproblem_structure.SUBPROBLEM_STAGES.keys()) == [
        1
    ] and subproblem_structure.SUBPROBLEM_STAGES[subproblem] == [1]:
        subproblem_directory = ""
    else:
        subproblem_directory = str(subproblem)

    # If no stages in this subproblem (empty list), run the
    # subproblem
    if subproblem_structure.SUBPROBLEM_STAGES[subproblem] == [1]:
        stage_directory = ""
        objective_values[subproblem] = run_optimization_for_subproblem_stage(
            scenario_directory,
            subproblem_directory,
            stage_directory,
            parsed_arguments,
        )
    # Otherwise, run the stage problem
    else:
        for stage in subproblem_structure.SUBPROBLEM_STAGES[subproblem]:
            stage_directory = str(stage)
            objective_values[subproblem][stage] = run_optimization_for_subproblem_stage(
                scenario_directory,
                subproblem_directory,
                stage_directory,
                parsed_arguments,
            )


def run_optimization_for_subproblem_pool(pool_datum):
    """
    Helper function to easily pass to pool.map if solving subproblems in
    parallel
    """
    [
        scenario_directory,
        subproblem_structure,
        subproblem,
        parsed_arguments,
        objective_values,
    ] = pool_datum

    run_optimization_for_subproblem(
        scenario_directory=scenario_directory,
        subproblem_structure=subproblem_structure,
        subproblem=subproblem,
        parsed_arguments=parsed_arguments,
        objective_values=objective_values,
    )


def run_scenario(
    scenario_directory,
    subproblem_structure,
    parsed_arguments,
):
    """
    Check the scenario structure, iterate over all subproblems if they
    exist, and run the subproblem optimization.

    The objective function is returned, but it's only really used if we
    are in 'testing' mode.

    :param scenario_directory: scenario directory path
    :param subproblem_structure: the subproblem structure object
    :param parsed_arguments:
    :return: the objective function value (NPV); only used in
     'testing' mode.
    """
    try:
        n_parallel_subproblems = int(parsed_arguments.n_parallel_solve)
    except ValueError:
        warnings.warn(
            "The argument '--n_parallel_subproblems' must be "
            "an integer. Solving subproblems sequentially."
        )
        n_parallel_subproblems = 1

    # If only a single subproblem, run main problem
    if list(subproblem_structure.SUBPROBLEM_STAGES.keys()) == [1]:
        if n_parallel_subproblems > 1:
            warnings.warn(
                "GridPath WARNING: only a single subproblem in "
                "scenario. No parallelization possible."
            )
        n_parallel_subproblems = 1
    else:
        pass

    # If parallelization is not requested, solve sequentially
    if n_parallel_subproblems == 1:
        # Create dictionary with which we'll keep track of subproblem/stage
        # objective function values
        objective_values = {}

        for subproblem in list(subproblem_structure.SUBPROBLEM_STAGES.keys()):
            objective_values[subproblem] = {}
            run_optimization_for_subproblem(
                scenario_directory=scenario_directory,
                subproblem_structure=subproblem_structure,
                subproblem=subproblem,
                parsed_arguments=parsed_arguments,
                objective_values=objective_values,
            )

        # Should probably just remove this logic here and have a dictionary
        # for all objective functions
        if len(objective_values.keys()) == 1:
            objective_values = objective_values[1]

        return objective_values

    # If parallelization is requested, proceed with some checks
    elif n_parallel_subproblems > 1:
        # Check if the subproblems are linked, in which case
        # we can't parallelize and throw a warning, then solve
        # sequentially
        if os.path.exists(
            os.path.join(scenario_directory, "linked_subproblems_map.csv")
        ):
            warnings.warn(
                "GridPath WARNING: subproblems are linked and "
                "cannot be solved in parallel. Solving "
                "sequentially."
            )
            # Solve sequentially
            objective_values = {}
            for subproblem in list(subproblem_structure.SUBPROBLEM_STAGES.keys()):
                run_optimization_for_subproblem(
                    scenario_directory=scenario_directory,
                    subproblem_structure=subproblem_structure,
                    subproblem=subproblem,
                    parsed_arguments=parsed_arguments,
                    objective_values=objective_values,
                )

            if len(objective_values.keys()) == 1:
                objective_values = objective_values[1]

            return objective_values

        # If subproblems are independent, we create pool of subproblems
        # and solve them in parallel
        else:
            # Create dictionary with which we'll keep track
            # of subproblem objective function values
            manager = Manager()
            objective_values = manager.dict()

            for subproblem in subproblem_structure.SUBPROBLEM_STAGES.keys():
                objective_values[subproblem] = manager.dict()

            # Pool must use spawn to work properly on Linux
            pool = get_context("spawn").Pool(n_parallel_subproblems)
            pool_data = tuple(
                [
                    [
                        scenario_directory,
                        subproblem_structure,
                        subproblem,
                        parsed_arguments,
                        objective_values,
                    ]
                    for subproblem in subproblem_structure.SUBPROBLEM_STAGES.keys()
                ]
            )

            pool.map(run_optimization_for_subproblem_pool, pool_data)
            pool.close()

            return objective_values


def save_results(
    scenario_directory,
    subproblem,
    stage,
    instance,
    results,
    dynamic_components,
    parsed_arguments,
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance: model instance (solution loaded after solving by default)
    :param dynamic_components:
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
    results_directory = os.path.join(
        scenario_directory, str(subproblem), str(stage), "results"
    )
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    # Check if a solution was found and only export results if so; save the
    # solver status, which will be used to determine the behavior of other
    # scripts
    with open(
        os.path.join(results_directory, "solver_status.txt"), "w", newline=""
    ) as f:
        f.write(str(results.solver.status))
    with open(
        os.path.join(results_directory, "termination_condition.txt"), "w", newline=""
    ) as f:
        f.write(str(results.solver.termination_condition))

    if results.solver.status == SolverStatus.ok:
        if not parsed_arguments.quiet:
            print(
                "Solver termination condition: {}.".format(
                    results.solver.termination_condition
                )
            )
            if results.solver.termination_condition == TerminationCondition.optimal:
                print("Optimal solution found.")
            else:
                print("Solution is not optimal.")
        # Continue with results export
        # Parse arguments to see if we're following a special rule for whether to
        # export results
        if parsed_arguments.results_export_rule is None:
            export_rule = _export_rule(instance=instance, quiet=parsed_arguments.quiet)
        else:
            export_rule = import_export_rules[parsed_arguments.results_export_rule][
                "export"
            ](instance=instance, quiet=parsed_arguments.quiet)
        export_results(
            scenario_directory,
            subproblem,
            stage,
            instance,
            dynamic_components,
            export_rule,
        )

        export_pass_through_inputs(scenario_directory, subproblem, stage, instance)

        save_objective_function_value(scenario_directory, subproblem, stage, instance)

        save_duals(scenario_directory, subproblem, stage, instance)
    # If solver status is not ok, don't export results and print some
    # messages for the user
    else:
        if results.solver.termination_condition == TerminationCondition.infeasible:
            if not parsed_arguments.quiet:
                print(
                    "Problem was infeasible. Results not exported for "
                    "subproblem {}, stage {}.".format(subproblem, stage)
                )
            # If subproblems are linked, exit since we don't have linked inputs
            # for the next subproblem; otherwise, move on to the next
            # subproblem
            if os.path.exists(
                os.path.join(scenario_directory, "linked_subproblems_map.csv")
            ):
                raise Exception(
                    "Subproblem {}, stage {} was infeasible. "
                    "Exiting linked subproblem run.".format(subproblem, stage)
                )
            else:
                pass


def create_abstract_model(
    model, dynamic_components, loaded_modules, scenario_directory, subproblem, stage
):
    """
    :param model: the Pyomo AbstractModel object
    :param dynamic_components: the populated dynamic model components class
    :param loaded_modules: list of the required modules as Python objects
    :param scenario_directory:
    :param subproblem:
    :param stage:

    To create the abstract model, we iterate over all required modules and
    call their *add_model_components* method to add components to the Pyomo
    AbstractModel. Some modules' *add_model_components* method also require the
    dynamic component class as an argument for any dynamic components to be
    added to the model.
    """
    for m in loaded_modules:
        if hasattr(m, "add_model_components"):
            m.add_model_components(
                model, dynamic_components, scenario_directory, subproblem, stage
            )


def load_scenario_data(
    model, dynamic_components, loaded_modules, scenario_directory, subproblem, stage
):
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
            m.load_model_data(
                model,
                dynamic_components,
                data_portal,
                scenario_directory,
                subproblem,
                stage,
            )
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


def fix_variables(
    instance, dynamic_components, scenario_directory, subproblem, stage, loaded_modules
):
    """
    :param instance: the compiled problem instance
    :param dynamic_components: the dynamic component class
    :param scenario_directory: str
    :param subproblem: str
    :param stage: str
    :param loaded_modules: list of imported GridPath modules as Python objects
    :return: the problem instance with the relevant variables fixed

    Iterate over the required GridPath modules and fix variables by calling
    the modules' *fix_variables*, if applicable. Return the modified
    problem instance with the relevant variables fixed.
    """
    for m in loaded_modules:
        if hasattr(m, "fix_variables"):
            m.fix_variables(
                instance, dynamic_components, scenario_directory, subproblem, stage
            )
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
        scenario_name=parsed_arguments.scenario,
    )
    solver_options = dict()
    solver_options_file = os.path.join(scenario_directory, "solver_options.csv")

    # First, figure out which solver or shell solver (solver_name) we are using and do
    # some checks
    # The solver_name is simply the chosen "optimizer," e.g. Cbc, Gurobi, CPLEX,
    # or a shell solver such as GAMS and AMPL
    # This is separate from a "solver" option, which is the solver to use if using a
    # shell solver such as GAMS
    if os.path.exists(solver_options_file):
        with open(solver_options_file) as f:
            _reader = reader(f, delimiter=",")
            for row in _reader:
                solver_options[row[0]] = row[1]

        # Check the the solver name specified is the same as that given from the
        # command line (if any)
        if parsed_arguments.solver is not None:
            if parsed_arguments.solver == solver_options["solver_name"]:
                pass
            else:
                raise UserWarning(
                    "ERROR! Solver specified on command line ({}) and solver name "
                    "in solver_options.csv ({}) do not match.".format(
                        parsed_arguments.solver, solver_options["solver_name"]
                    )
                )

        # If we make it here, set the solver name from the
        # solver_options.csv file
        solver_name = solver_options["solver_name"]
        # remove "solver_name" from the solver_options object, as it is not actually
        # an "option" and we can iterate over options later without worrying about
        # skipping this
        del solver_options["solver_name"]

    else:
        if parsed_arguments.solver is None:
            solver_name = "cbc"

    # Get solver
    # If a solver executable is specified, pass it to Pyomo
    if parsed_arguments.solver_executable is not None:
        optimizer = SolverFactory(
            solver_name, executable=parsed_arguments.solver_executable
        )
    # Otherwise, only pass the solver name; Pyomo will look for the
    # executable in the PATH
    else:
        optimizer = SolverFactory(solver_name)

    # Solve
    # Apply the solver options (if any)
    # Note: Pyomo moves the results to the instance object by default.
    # If you want the results to stay into a results object, set the
    # load_solutions argument to False:
    # >>> results = solver.solve(instance, load_solutions=False)
    # With "shell solvers" (e.g. GAMS, AMPL), we can specify which solver (e.g.
    # CPLEX, Gurobi) to use
    # No access to AMPL, so not supported at this pont
    if solver_name == "gams":
        # Specify which "solver" to use if using GAMS as a "shell solver" --
        # e.g. we could be using CPLEX through GAMS
        # The following way to pass options to the solver is GAMS-specific, may also
        # work for AMPL but not supported at this point
        # Based on: https://stackoverflow.com/questions/57965894/how-to-specify-gams-solver-specific-options-through-pyomo/64698920#64698920
        if "solver" in solver_options.keys():
            add_options = [
                "GAMS_MODEL.optfile = 1;",
                "$onecho > {solver}.opt".format(solver=solver_options["solver"]),
            ]
            for opt in solver_options.keys():
                if opt == "solver":
                    pass
                else:
                    opt_string = "{option} {value}".format(
                        option=opt, value=solver_options[opt]
                    )
                    add_options.append(opt_string)

            add_options.append("$offecho")

            results = optimizer.solve(
                instance,
                solver=solver_options["solver"],
                add_options=add_options,
                tee=not parsed_arguments.mute_solver_output,
                keepfiles=parsed_arguments.keepfiles,
                symbolic_solver_labels=parsed_arguments.symbolic,
            )
        else:
            warnings.warn(
                "A solver must be specified in the solver settings if you "
                "want to pass settings through GAMS."
            )
    else:
        for opt in solver_options.keys():
            optimizer.options[opt] = solver_options[opt]

        results = optimizer.solve(
            instance,
            tee=not parsed_arguments.mute_solver_output,
            keepfiles=parsed_arguments.keepfiles,
            symbolic_solver_labels=parsed_arguments.symbolic,
        )

    # Can optionally log infeasibilities but this has resulted in false
    # positives due to rounding errors larger than the default tolerance
    # of 1E-6.
    # log_infeasible_constraints(instance)

    return results


def export_results(
    scenario_directory, subproblem, stage, instance, dynamic_components, export_rule
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance:
    :param dynamic_components:
    :return:

    Export results for each loaded module (if applicable)
    """
    if export_rule:
        # Determine/load modules and dynamic components
        modules_to_use, loaded_modules = set_up_gridpath_modules(
            scenario_directory=scenario_directory, subproblem=subproblem, stage=stage
        )

        for m in loaded_modules:
            if hasattr(m, "export_results"):
                m.export_results(
                    scenario_directory, subproblem, stage, instance, dynamic_components
                )
        else:
            pass


def export_pass_through_inputs(scenario_directory, subproblem, stage, instance):
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
    modules_to_use, loaded_modules = set_up_gridpath_modules(
        scenario_directory=scenario_directory, subproblem=subproblem, stage=stage
    )

    for m in loaded_modules:
        if hasattr(m, "export_pass_through_inputs"):
            m.export_pass_through_inputs(
                scenario_directory, subproblem, stage, instance
            )
    else:
        pass


def save_objective_function_value(scenario_directory, subproblem, stage, instance):
    """
    Save the objective function value.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param instance:
    :return:
    """
    objective_function_value = instance.NPV()

    # Round objective function value of test examples
    if os.path.dirname(scenario_directory)[-8:] == "examples":
        objective_function_value = round(objective_function_value, 2)

    with open(
        os.path.join(
            scenario_directory,
            subproblem,
            stage,
            "results",
            "objective_function_value.txt",
        ),
        "w",
        newline="",
    ) as objective_file:
        objective_file.write("Objective function: " + str(objective_function_value))
        # TODO: change to writing the value only when we implement importing
        #  the objective function value into the results_scenario table
        # objective_file.write(str(objective_function_value))


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
    modules_to_use, loaded_modules = set_up_gridpath_modules(
        scenario_directory=scenario_directory, subproblem=subproblem, stage=stage
    )

    instance.constraint_indices = {}
    for m in loaded_modules:
        if hasattr(m, "save_duals"):
            m.save_duals(instance)
        else:
            pass

    for c in list(instance.constraint_indices.keys()):
        constraint_object = getattr(instance, c)
        with open(
            os.path.join(
                scenario_directory, subproblem, stage, "results", str(c) + ".csv"
            ),
            "w",
            newline="",
        ) as duals_results_file:
            duals_writer = writer(duals_results_file)
            duals_writer.writerow(instance.constraint_indices[c])
            for index in constraint_object:
                try:
                    duals_writer.writerow(
                        list(index) + [instance.dual[constraint_object[index]]]
                    )
                # We get an error when trying to export duals with CPLEX
                # when solving MIPs, so catch it here and ignore to avoid
                # breaking the script, but throw a warning
                except KeyError:
                    warnings.warn(
                        """
                    KeyError caught when saving duals. Duals were not exported.
                    This is expected if solving a MIP with CPLEX, 
                    not otherwise.
                    """
                    )
                    pass


def summarize_results(scenario_directory, subproblem, stage, parsed_arguments):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param parsed_arguments:
    :return:

    Summarize results (after results export)
    """
    if parsed_arguments.results_export_rule is None:
        summarize_rule = _summarize_rule(
            scenario_directory=scenario_directory,
            subproblem=subproblem,
            stage=stage,
            quiet=parsed_arguments.quiet,
        )
    else:
        summarize_rule = import_export_rules[parsed_arguments.results_export_rule][
            "summarize"
        ](
            scenario_directory=scenario_directory,
            subproblem=subproblem,
            stage=stage,
            quiet=parsed_arguments.quiet,
        )

    if summarize_rule:
        # Only summarize results if solver status was "optimal"
        with open(
            os.path.join(
                scenario_directory, subproblem, stage, "results", "solver_status.txt"
            ),
            "r",
        ) as f:
            solver_status = f.read()

        if solver_status == "ok":
            if not parsed_arguments.quiet:
                print("Summarizing results...")

            # Determine/load modules and dynamic components
            modules_to_use, loaded_modules = set_up_gridpath_modules(
                scenario_directory=scenario_directory,
                subproblem=subproblem,
                stage=stage,
            )

            # Make the summary results file
            summary_results_file = os.path.join(
                scenario_directory, subproblem, stage, "results", "summary_results.txt"
            )

            # TODO: how to handle results from previous runs
            # Overwrite prior results
            with open(summary_results_file, "w", newline="") as outfile:
                outfile.write(
                    "##### SUMMARY RESULTS FOR SCENARIO *{}* #####\n".format(
                        parsed_arguments.scenario
                    )
                )

            # Go through the modules and get the appropriate results
            for m in loaded_modules:
                if hasattr(m, "summarize_results"):
                    m.summarize_results(scenario_directory, subproblem, stage)
            else:
                pass
        else:
            pass


def set_up_gridpath_modules(scenario_directory, subproblem, stage):
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
    # populate_dynamic_inputs(dynamic_components, loaded_modules,
    #                         scenario_directory, subproblem, stage)

    return modules_to_use, loaded_modules


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
        parents=[
            get_scenario_name_parser(),
            get_required_e2e_arguments_parser(),
            get_run_scenario_parser(),
        ],
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

    scenario_directory = determine_scenario_directory(
        scenario_location=parsed_args.scenario_location,
        scenario_name=parsed_args.scenario,
    )

    # Check if the scenario actually exists
    if not os.path.exists(scenario_directory):
        raise IOError(
            "Scenario '{}/{}' does not exist. Please verify"
            " scenario name and scenario location".format(
                parsed_args.scenario_location, parsed_args.scenario
            )
        )

    subproblem_structure = get_subproblem_structure_from_disk(
        scenario_directory=scenario_directory
    )

    # Run the scenario (can be multiple optimization subproblems)
    expected_objective_values = run_scenario(
        scenario_directory=scenario_directory,
        subproblem_structure=subproblem_structure,
        parsed_arguments=parsed_args,
    )

    # Return the objective function values (used in testing)
    return expected_objective_values


def _export_rule(instance, quiet):
    """
    :return: boolean

    Rule for whether to export results for the current proble. Write your
    custom rule here to use this functionality. Must return True or False.
    """
    export_results = True

    return export_results


def _summarize_rule(scenario_directory, subproblem, stage, quiet):
    """
    :return: boolean

    Rule for whether to summarize results for a subproblem/stage. Write your
    custom rule here to use this functionality. Must return True or False.
    """
    summarize_results = True

    return summarize_results


if __name__ == "__main__":
    main()
