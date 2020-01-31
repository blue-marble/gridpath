#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Testing class

This will be a classs that will contain all other info that is needed
to run something. It will have attributes that contain this information,
some of which could be classes themselves

The following code that is repeated in many scripts should all be done
when initializing the Scenario Class Object:

scenario_id, scenario_name = get_scenario_id_and_name(
    scenario_id_arg=scenario_id_arg,
    scenario_name_arg=scenario_name_arg,
    c=c,
    script="get_scenario_inputs"
)

# Determine scenario directory and create it if needed
scenario_directory = determine_scenario_directory(
    scenario_location=scenario_location,
    scenario_name=scenario_name
)
create_directory_if_not_exists(directory=scenario_directory)

optional_features = OptionalFeatures(cursor=c, scenario_id=scenario_id)
subscenarios = SubScenarios(cursor=c, scenario_id=scenario_id)
subproblems = SubProblems(cursor=c, scenario_id=scenario_id)
solver_options = SolverOptions(cursor=c, scenario_id=scenario_id)


TODO: get_scenario_inputs.py, process_results.py, etc. can all become
  methods to this class. We can still have separate script files to invoke
  these methods separately in the commande line. In that script, all we
  would do is parse arguments, create the Scenario class object, and
  invoke the method.

"""

from builtins import object
import csv
import os
import pandas as pd
from pyomo.environ import AbstractModel, Suffix, DataPortal, SolverFactory
import sys


import gridpath.auxiliary.scenario_chars as sc
from gridpath.auxiliary.module_list import determine_modules, load_modules


class Scenario(object):

    def __init__(self, conn=None, scenario_id=None,
                 scenario_name=None, scenario_dir=None):
        """
        Need to provide either a database connection and scenario id
        OR scenario location and name
        (maybe create 2 types of classes with different methods for each?
        One if scenario created from database, one if created from files?
        """

        self.conn = conn
        self.scenario_id = scenario_id  # TODO: add way to add scenario name
        # smarter way? (i.e. move get_scenario id and name here?)
        self.scenario_name = scenario_name
        self.scenario_dir = scenario_dir

        # Start with empty dynamic components
        self.dynamic_components = DynamicComponents()
        self.dynamic_components_added = False  # flag, true after we run "determine_dynamic_components"

        # State variables
        self.active_subproblem = None
        self.active_stage = None
        self.has_subproblems = False

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
        self.optional_features = self.init_optional_features()
        self.subscenarios = self.init_subscenarios()
        self.subproblems = self.init_subproblems()
        self.solver_options = self.init_solver_options()

        self.loaded_modules = load_modules(
            determine_modules(self.optional_features)
        )

    # TODO: question: could also make this not return anything but instead
    #  do the attribute assignment here. But that's more unclear?
    def init_optional_features(self):
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

    # Init functions (constructors?)
    ###########################################################################

    def init_subscenarios(self):
        # cannot create this without database!
        if self.conn is None or self.scenario_id is None:
            # no subscenarios when creating scenario from DB!
            return None
        else:
            return sc.SubScenarios(self.conn, self.scenario_id)

    def init_solver_options(self):
        if self.conn is None or self.scenario_id is None:
            return sc.SolverOptions(self.conn, self.scenario_id)
        else:
            return []  # need to derive it from file and do some checks
            # see run_scenario for what happens (?)

    def init_subproblems(self):
        if self.conn is None or self.scenario_id is None:
            return sc.SubProblems(self.conn, self.scenario_id)
        else:
            return []  # TODO: need to derive it from file structure,
            # as is done in the run_scenario_script

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

    def create_inputs_structure(self):
        # create the tiered input file structure based on the subproblem
        # scenario structure. Can't use this if you're initializing from
        # file (since should already be there!)
        pass

    def write_model_inputs(self):
        """
        For each module, load the inputs from the database and write out the inputs
        into .tab files, which will be used to construct the optimization
        problem.
        :return:
        """
        # can only call this with database and scenario specified
        # see get_scenario_inputs.py, but break out creating the file
        # strucutr perhaps?
        pass

    # Model Setup

    def populate_dynamic_components(self, subproblem, stage):
        # can only call this when scenario_dir is defined and we have input
        # files!
        # TODO: how to handle subproblem and stage
        # TODO: might want to rename determine_dynamic_components to something
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
        :param model: the Pyomo abstract model object with components added
        :param subproblem: the horizon subproblem
        :param stage: the stage subproblem
        :return: the compiled model instance

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
