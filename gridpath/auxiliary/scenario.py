#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This will be a class that will contain all "meta data" that is needed
to run a scenario (can be multiple runs). It will have attributes that contain
this information, some of which could be classes themselves such as
Subproblems or OptionalFeatures.

Advantages:
 - avoid many of the repetitive code in get_scenario_inputs.py,
 process_results.py, etc. where we do the same loading of modules,
 determining scenario name/id/dir etc., over an over.
 - encapsulate all the information for running a scenario into one object
 rather than having to pass around dynamic components, loaded modules,
 scenario directories, etc.
 - might allow for cleaner way on how to deal with (sub) problems. The
 scenario class might hold info on whether we have any and the structure.
- if we ever change how subproblems ands stages are organized, this approach
  will make it easier to update code hwne we do (only one or tow functions vs.
  a bunch of stuff scattered across files)

We can still have separate script files to invoke these methods separately
in the command line. In that script, all we would do is parse arguments,
create the Scenario class object, and invoke the method.

Issues encountered:
 - object can be created from 2 different ways of data: 1. from the database
 directly (in which case you need connection and scenario_id), or from
 file (e.g. when running run_scenario.py) in which case you need the metadata
 in auxiliary csv files (features.csv, subproblems.csv etc.)
 - class might get very big?

One solution would be to have a master Scenario class, and then 2 subclasses
one is scenario_from_db, another one is scenario_from_file.

General issues (not necessarily related to this):
 - terminology between scenario, optimization, (sub)problem, subproblem
 etc. is confusing and not always consistent. Should clarify somewhere
 what we mean by each and perhaps think of cleaner names for some.
 (e.g. subproblems.csv is also used to designate stage (sub) problems that
 you have to optimize independently).
 - Need to explain scenario_location, scenario_dir, and inputs/results_dir,
 and relation to the terms above.

"""

from builtins import object
import csv
import os
import pandas as pd
from pyomo.environ import AbstractModel, Suffix, DataPortal, SolverFactory
import sys


import gridpath.auxiliary.scenario_chars as sc
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.common_functions import determine_scenario_directory
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name



class Scenario(object):
    # TODO: dynamic components class could hold info on active subproblem
    #   and stage, so we don't have to pass subproblem and stage around
    #   explicitly everywhere?
    # TODO: could have 2 subclasse? One is for scenario from file, one is for
    #   scenario from database?
    def __init__(self, conn=None, scenario_id=None,
                 scenario_name=None, scenario_location=None):
        """
        Need to provide either a database connection and scenario id
        OR scenario location and name
        """
        self.conn = conn
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.scenario_location = scenario_location

        # TODO: this doesn't work if you are running from file (run_scenario)
        self.scenario_id, self.scenario_name = get_scenario_id_and_name(
            scenario_id_arg=scenario_id,
            scenario_name_arg=scenario_name,
            c=self.conn.cursor(), script="scenario.py")

        self.scenario_dir = determine_scenario_directory(
            scenario_location=scenario_location,
            scenario_name=scenario_name
        )
        # TODO: create directory if it doesn't exist?

        # flag to know whether we can get all our init info from database
        # If not, GridPath will try to get scenario info from file(s)
        self.db_scenario_identified = self.init_db_scenario_identified()


        # Start with empty dynamic components
        self.dynamic_components = DynamicComponents()
        self.dynamic_components_populated = False  # flag, true after we run
        # "determine_dynamic_components"

        # State variables
        self.active_subproblem = None  # TODO: just an idea
        self.active_stage = None  # TODO: just an idea
        self.has_subproblems = False  # TODO: just an idea
        self.results_exported = False
        # TODO: Make this true if there ar results files present (and after
        #  running export results (already done)

        # TODO: problem is that a lot of class inits require database which is
        #  a problem if you want to simply do run_scenario off the tab files
        #  The core reason is we have this awkward DB to .tab file interface
        #  which writes out a lot of this stuff (e.g. solver options) into
        #  csv files so you can do these things without CSV files
        # optional features: used in determine modules. if running from DB,
        # we get it from class object, and pass it. If not, determine modules
        # will look for feature file, and get features from there. It's a bit
        # confusing that determine modules doesn't always use features as input
        # Solution: determine modules always uses list of features, but in
        # this init function we can determine the optional features depending
        # on what's given to us.
        # Similar for solver options (has csv file vs. getting from db)
        # subproblems is similar to ScenarioStructure!
        # TODO: also add optional_features class (not just list)
        self.optional_features = self._init_optional_features()
        self.subscenarios = self._init_subscenarios()
        self.subproblems = self._init_subproblems()
        self.solver_options = self._init_solver_options()

        self.loaded_modules = load_modules(
            determine_modules(self.optional_features)
        )


    # Init functions (constructors?)
    ###########################################################################

    def _init_db_scenario_identified(self):
        if self.conn is not None and (self.scenario_id is not None
                                      or self.scenario_name is not None):
            return True
        else:
            return False

    # TODO: question: could also make this not return anything but instead
    #  do the attribute assignment here. But that's more unclear?
    def _init_optional_features(self):
        if self.conn is None and self.scenario_id is None and \
                self.scenario_dir is None:
            raise IOError("Need to provide at least database connection and"
                          "scenario_id or scenario_directory to initialize"
                          "a Scenario class object")
        # TODO: deal with all cases better (could have scenario dir specified
        #  but still want to initailize off database?)
        elif self.conn is None or self.scenario_id is None:
            features_file = os.path.join(self.scenario_dir, "features.csv")
            try:
                return pd.read_csv(features_file)["features"].tolist()
            except IOError:
                print(
                    "ERROR! Features file {} not found in {}.".format(
                        features_file, self.scenario_dir)
                )
                sys.exit(1)
        else:
            of = sc.OptionalFeatures(self.conn, self.scenario_id)
            return of.determine_feature_list()

    def _init_subscenarios(self):
        # cannot create this without database!
        if self.conn is None or self.scenario_id is None:
            # no subscenarios when creating scenario from DB!
            return None
        else:
            return sc.SubScenarios(self.conn, self.scenario_id)

    def _init_solver_options(self):
        if self.conn is None or self.scenario_id is None:
            return sc.SolverOptions(self.conn, self.scenario_id)
        else:
            return []  # need to derive it from file and do some checks
            # see run_scenario for what happens (?)

    def _init_subproblems(self):
        if self.conn is None or self.scenario_id is None:
            return sc.SubProblems(self.conn, self.scenario_id)
        else:
            return []  # TODO: need to derive it from file structure,
                       #  as is done in the run_scenario_script

    # Module level functions
    ###########################################################################

    def validate_inputs(self):
        """"
        For each module, load the inputs from the database and validate them
        """
        if self.subscenarios is None:
            raise IOError("Need subscenarios specified for validation")
        subproblems_list = self.subproblems.SUBPROBLEMS
        for subproblem in subproblems_list:
            stages = self.subproblems.SUBPROBLEM_STAGE_DICT[subproblem]
            for stage in stages:
                # 1. input validation within each module
                for m in self.loaded_modules:
                    if hasattr(m, "validate_inputs"):
                        m.validate_inputs(
                            subscenarios=self.subscenarios,
                            subproblem=subproblem,
                            stage=stage,
                            conn=self.conn
                        )
                    else:
                        pass

                # 2. input validation across modules
                #    make sure geography and projects are in line
                #    ... (see Evernote validation list)
                #    create separate function for each validation that you call here


    def write_model_inputs(self):
        """
        For each module, load the inputs from the database and write out the
        inputs into .tab files, which will be used to construct the
        optimization problem.
        """

        delete_prior_aux_files(scenario_directory=self.scenario_dir)

        inputs_dirs = self.get_subproblem_directories("inputs")
        # TODO: write out subproblem/stage strucutre file that specifie whole
        #  sturcture in the base_dir. (not a nested set of .csv files like now)

        for subproblem, stage in inputs_dirs.keys():
            inputs_dir = inputs_dirs[(subproblem, stage)]
            if not os.path.exists(inputs_dir):
                os.makedirs(inputs_dir)

            delete_prior_inputs(inputs_directory=inputs_dir)

            # Write model input .tab files for each of the loaded_modules if
            # appropriate. Note that all input files are saved in the
            # input_directory, even the non-temporal inputs that are not
            # dependent on the subproblem or stage. This simplifies the file
            # structure at the expense of unnecessarily duplicating non-temporal
            # input files such as projects.tab.
            for m in self.loaded_modules:
                if hasattr(m, "write_model_inputs"):
                    m.write_model_inputs(
                        inputs_directory=inputs_dir,
                        subscenarios=self.subscenarios,
                        subproblem=subproblem,
                        stage=stage,
                        conn=self.conn,
                    )
                else:
                    pass

    def get_subproblem_directories(self, data_type):
        """
        When there are multiple subproblems and/or stages,
        the subproblem inputs and results files will be in nested dirs
        :param data_type: "input" or "output"  # TODO: validate this!
        :return: dictionary with directory by subproblem/stage

        TODO: make this part of separete scenario structure class?
        TODO: should we do this on init? (for both inputs and results)
        """
        dirs = {}  # TODO: should be ordered dict!
        subproblems_list = self.subproblems.SUBPROBLEMS
        for subproblem in subproblems_list:
            stages = self.subproblems.SUBPROBLEM_STAGE_DICT[subproblem]
            for stage in stages:
                # if there are subproblems/stages, input directory is nested
                if len(subproblems_list) > 1 and len(stages) > 1:
                    dirs[(subproblem, stage)] = os.path.join(
                        self.scenario_dir,
                        str(subproblem),
                        str(stage),
                        data_type
                    )
                elif len(self.subproblems.SUBPROBLEMS) > 1:
                    dirs[(subproblem, stage)] = os.path.join(
                        self.scenario_dir,
                        str(subproblem),
                        data_type
                    )
                elif len(stages) > 1:
                    dirs[(subproblem, stage)] = os.path.join(
                        self.scenario_dir,
                        str(stage),
                        data_type
                    )
                else:
                    dirs[(subproblem, stage)] = os.path.join(
                        self.scenario_dir,
                        data_type
                    )

        return dirs


    def populate_dynamic_components(self, subproblem, stage):
        """
        We iterate over all required modules and call their
        *determine_dynamic_components* method, if applicable, in order to add
        the dynamic components to the *dynamic_components* class object,
        which we will then pass to the *add_model_components* module methods,
        so that the applicable components can be added to the abstract model.
        """
        # can only call this when scenario_dir is defined and we have input
        # files!
        # TODO: how to handle subproblem and stage, move into dynamic comps?
        #  or simply pass the inputs dir, which is scenario_dir/subpr/stage
        #  Migh be possible here, but write_model_inputs or
        #  import_results_into_database need subproblem/stage to know in
        #  which database you are importing
        # TODO: might want to rename determine_dynamic_components to something
        # TODO: there are some functions that do similar stuff from the
        #  database, e.g. get_required_capacity_types

        # that is more clear about that it changes the dynamic components
        # in place.

        for m in self.loaded_modules:
            if hasattr(m, 'determine_dynamic_components'):
                m.determine_dynamic_components(self.dynamic_components,
                                               self.scenario_directory,
                                               subproblem,
                                               stage)
            else:
                pass

    def create_abstract_model(self):
        """
        To create the abstract model, we iterate over all required modules and
        call their *add_model_components* method to add components to the Pyomo
        AbstractModel. Some modules' *add_model_components* method also require
        the dynamic component class as an argument for any dynamic components
        to be added to the model.
        """
        model = AbstractModel()
        for m in self.loaded_modules:
            if hasattr(m, 'add_model_components'):
                m.add_model_components(model, self.dynamic_components)

        return model

    def load_scenario_data(self, model, subproblem, stage, quiet=False):
        """
        Iterate over all required GridPath modules and call their
        *load_model_data* method in order to load input data into the
        data portal. Use the data portal to instanciate the abstract model.
        """

        # Create Data Portal
        if not quiet:
            print("Loading data...")
        data_portal = DataPortal()
        for m in self.loaded_modules:
            if hasattr(m, "load_model_data"):
                m.load_model_data(model, self.dynamic_components, data_portal,
                                  self.scenario_dir, subproblem, stage)
            else:
                pass

        # Build the problem instance; this will also call any BuildActions that
        # construct the dynamic inputs
        # TODO: pretty sure there aren't any BuildActions left (?)
        if not quiet:
            print("Creating problem instance...")
        instance = model.create_instance(data_portal)

        return instance

    def fix_variables(self, instance):
        """
        :param instance: the compiled problem instance
        :return: the problem instance with the relevant variables fixed

        Iterate over the required GridPath modules and fix variables by calling
        the modules' *fix_variables*, if applicable. Return the modified
        problem instance with the relevant variables fixed.
        """
        for m in self.loaded_modules:
            if hasattr(m, "fix_variables"):
                m.fix_variables(instance, self.dynamic_components)
            else:
                pass

        return instance

    # After running model
    # TODO: rename moddel to instance?

    def export_results(self, model, subproblem, stage)
        """
        Export results for each loaded module (if applicable)
        """
        for m in self.loaded_modules:
            if hasattr(m, "export_results"):
                m.export_results(self.scenario_dir, subproblem, stage,
                                 model, self.dynamic_components)
        else:
            pass

        # TODO: index this by subproblem and stage?
        self.results_exported = True

    def export_pass_through_inputs(self, model, subproblem, stage):
        """
        Export pass through inputs for each loaded module (if applicable)
        """
        for m in self.loaded_modules:
            if hasattr(m, "export_pass_through_inputs"):
                m.export_pass_through_inputs(
                    self.scenario_dir, subproblem, stage,
                    model, self.dynamic_components
                )
        else:
            pass

    def save_duals(self, model, subproblem, stage):
        """
        Save the duals of various constraints.
        """
        model.constraint_indices = {}
        for m in self.loaded_modules:
            if hasattr(m, "save_duals"):
                m.save_duals(model)
            else:
                pass

        for c in list(model.constraint_indices.keys()):
            constraint_object = getattr(model, c)
            with open(os.path.join(
                    self.scenario_dir, subproblem, stage, "results",
                    str(c) + ".csv"),
                    "w", newline=""
            ) as duals_results_file:
                duals_writer = csv.writer(duals_results_file)
                duals_writer.writerow(model.constraint_indices[c])
                for index in constraint_object:
                    duals_writer.writerow(list(index) +
                                          [model.dual[
                                               constraint_object[index]]]
                                          )

    def summarize_results(self, subproblem, stage, quiet=False):
        """
        Summarize results (after results export)
        """
        if not quiet:
            print("Summarizing results...")

        # Make the summary results file
        summary_results_file = os.path.join(
            self.scenario_dir, subproblem, stage, "results",
            "summary_results.txt"
        )

        # TODO: how to handle results from previous runs
        # Overwrite prior results
        with open(summary_results_file, "w", newline="") as outfile:
            outfile.write(
                "##### SUMMARY RESULTS FOR SCENARIO *{}* #####\n".format(
                    self.scenario_name)
            )

        # Go through the modules and get the appropriate results
        for m in self.loaded_modules:
            if hasattr(m, "summarize_results"):
                m.summarize_results(self.dynamic_components,
                                    self.scenario_dir,
                                    subproblem,
                                    stage)
        else:
            pass


    def import_results_into_database(self):
        """

        :return:
        """
        if not self.db_scenario_identified:
            raise IOError("Scenario is not properly linked to database, "
                          "cannot import results into database")
        if not self.results_exported:
            raise IOError("No results to export. Run optimzation first")

        results_dirs = self.get_subproblem_directories("results")
        for subproblem, stage in results_dirs.keys():
            results_dir = results_dirs[(subproblem, stage)]

            if not os.path.exists(results_dir):
                os.makedirs(results_dir)

            for m in self.loaded_modules:
                if hasattr(m, "import_results_into_database"):
                    m.import_results_into_database(
                        scenario_id=self.scenario_id,
                        subproblem=subproblem,
                        stage=stage,
                        c=self.conn.cursor(),  # TODO: remove this?
                        db=self.conn,
                        results_directory=results_dir
                    )
                else:
                    pass


    def process_results(self):
        for m in self.loaded_modules:
            if hasattr(m, "process_results"):
                m.process_results(self.conn, self.subscenarios)
            else:
                pass

# TODO: is this really necessary? It seems like we could simply get rid
#  of the string assignment and directly assign things in the class init, e.g.
#  self.required_capacity_modules = list()
#  self.capacity_type_operational_period_sets = list()
#  That way we also don't really have to import anything when we use these
#  sets but simply say d.required_capacity_modules = df.capacity_type.unique()


# TODO: should we have more than one of these depending on component type,
#  e.g. a group for GP modules to use (e.g. capacity and operational types,
#  prm modules, reserve modules) vs. actual optimizaton model components such
#  as the headroom and footroom variables vs. the names of constraint
#  components

class DynamicComponents(object):
    """
    Here we initialize the class object and its components that will contain
    the dynamic inputs. When called, the GridPath modules will populate the
    various class components based on the input data, which will then be
    used to initialize model components, keep track of required submodules,
    keep track of components added by modules to dynamic constraints, etc.
    """
    def __init__(self):
        """
        Initialize the dynamic components.
        """

        # ### Types ### #

        # Capacity-type modules (the list of unique capacity types in the
        # project list)
        self.required_capacity_modules = list()
        # Capacity-type modules will populate these lists if called
        # These are the sets of project-operational_period by capacity type;
        # the sets will be joined to make the final
        # project-operational_period set that includes all projects
        self.capacity_type_operational_period_sets = list()
        self.storage_only_capacity_type_operational_period_sets = list()

        # Availability type modules (the list of unique availability types in
        # the project list)
        self.required_availability_modules = list()

        # Operational type modules (the list of unique operational types in
        # the project list)
        self.required_operational_modules = list()

        # PRM type modules (the list of unique prm types in the project list)
        self.required_prm_modules = list()

        # PRM cost groups
        self.prm_cost_group_sets = list()
        self.prm_cost_group_prm_type = dict()

        # Transmission
        self.required_tx_capacity_modules = list()
        self.required_tx_operational_modules = list()

        # ### Operating reserves ### #

        # Reserve types -- the list of reserve types the user has requested
        # to be modeled
        # Will be determined based on whether the user has specified a module
        # This list is populated in
        # *gridpath.operations.reserves.reserve_provision* when the respective
        # reserve module is called (e.g. spinning reserves are added to this
        # list when *gridpath.operations.reserves.spinning_reserves* is
        # called, which in turn only happens if the 'spinning_reserves'
        # feature is selected
        self.required_reserve_modules = list()

        # Headroom and footroom variables
        # These will include the project as keys and a list as value for
        # each project; the list could be empty if the project is not
        # providing any reserves, or will include the names of the
        # respective reserve-provision variable if the reserve-type is
        # modeled and a project can provide it
        self.headroom_variables = dict()
        self.footroom_variables = dict()

        # A reserve-provision derate parameter and a
        # reserve-to-energy-adjustment parameter could also be assigned to
        # project, so we make dictionaries that will link the
        # reserve-provision variable names to a derate-param name (i.e. the
        # regulation up variable will be linked to a regulation-up
        # parameter, the spinning-reserves variable will be linked to a
        # spinning reserves paramater, etc.)
        self.reserve_variable_derate_params = dict()
        self.reserve_to_energy_adjustment_params = dict()

        # ### Constraint and objective function components ### #

        # Load balance constraint
        # Modules will add component names to these lists
        self.load_balance_production_components = list()
        self.load_balance_consumption_components = list()

        # Carbon cap constraint
        # Modules will add component names to these lists
        self.carbon_cap_balance_emission_components = list()

        # PRM constraint
        # Modules will add component names to this list
        self.prm_balance_provision_components = list()

        # Local capacity constraint
        # Modules will add component names to this list
        self.local_capacity_balance_provision_components = list()

        # Objective function
        # Modules will add component names to this list
        self.total_cost_components = list()


def delete_prior_aux_files(scenario_directory):
    """
    Delete all auxiliary files that may exist in the scenario directory
    :param scenario_directory: the scenario directory
    :return:
    """
    prior_aux_files = [
        "features.csv", "scenario_description.csv", "scenario_id.txt",
        "solver_options.csv"
    ]

    for f in prior_aux_files:
        if f in os.listdir(scenario_directory):
            os.remove(os.path.join(scenario_directory, f))
        else:
            pass

def delete_prior_inputs(inputs_directory):
    """
    Delete all .tab files that may exist in the specified directory
    :param inputs_directory: local directory where .tab files are saved
    :return:
    """
    prior_input_tab_files = [
        f for f in os.listdir(inputs_directory) if f.endswith('.tab')
    ]

    for f in prior_input_tab_files:
        os.remove(os.path.join(inputs_directory, f))


def write_subproblems_csv(scenario_directory, subproblems):
    """
    Write the subproblems.csv file that will be used when solving multiple
    subproblems/stages in 'production cost' mode.

    TODO: rather than write nested subproblems.csv file, simply write a
     master file with the subproblem_stage structure the same way as the
     database has it. That way you can use same function as db to determine
     the scenario structure
    :return:
    """

    if not os.path.exists(scenario_directory):
        os.makedirs(scenario_directory)
    with open(os.path.join(scenario_directory, "subproblems.csv"),
              "w", newline="") as subproblems_csv_file:
        writer = csv.writer(subproblems_csv_file, delimiter=",")

        # Write header
        writer.writerow(["subproblems"])

        for subproblem in subproblems:
            writer.writerow([subproblem])


def write_features_csv(scenario_directory, feature_list):
    """
    Write the features.csv file that will be used to determine which
    GridPath modules to include
    :return:
    """
    with open(os.path.join(scenario_directory, "features.csv"),
              "w", newline="") as features_csv_file:
        writer = csv.writer(features_csv_file, delimiter=",")

        # Write header
        writer.writerow(["features"])

        for feature in feature_list:
            writer.writerow([feature])