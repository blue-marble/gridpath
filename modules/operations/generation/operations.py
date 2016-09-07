#!/usr/bin/env python

"""
Describe operational constraints on the generation infrastructure.
"""
import os.path
from csv import reader
from pandas import read_csv

from pyomo.environ import Set, Var, Expression, Constraint, NonNegativeReals

from auxiliary import check_list_items_are_unique, \
    find_list_item_position, make_gen_tmp_var_df, \
    load_operational_modules


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """
    Determine which operational type modules will be needed based on the
    operational types in the input data.
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # Generator capabilities
    d.headroom_variables = dict()
    d.footroom_variables = dict()

    with open(os.path.join(scenario_directory, "inputs", "generators.tab"),
              "rb") as generation_capacity_file:
        generation_capacity_reader = reader(generation_capacity_file,
                                            delimiter="\t")
        headers = generation_capacity_reader.next()
        # Check that columns are not repeated
        check_list_items_are_unique(headers)
        for row in generation_capacity_reader:
            # Get generator name; we have checked that columns names are unique
            # so can expect a single-item list here and get 0th element
            generator = row[find_list_item_position(headers, "GENERATORS")[0]]
            # All generators get the following variables
            d.headroom_variables[generator] = list()
            d.footroom_variables[generator] = list()
            # In addition, some generators get the variables associated with
            # provision of other services (e.g. reserves) if flagged
            # Generators that can provide upward load-following reserves
            if int(row[find_list_item_position(headers,
                                               "lf_reserves_up")[0]]
                   ):
                d.headroom_variables[generator].append(
                    "Provide_LF_Reserves_Up_MW")
            # Generators that can provide upward regulation
            if int(row[find_list_item_position(headers, "regulation_up")[0]]
                   ):
                d.headroom_variables[generator].append(
                    "Provide_Regulation_Up_MW")
            # Generators that can provide downward load-following reserves
            if int(row[find_list_item_position(headers, "lf_reserves_down")[0]]
                   ):
                d.footroom_variables[generator].append(
                    "Provide_LF_Reserves_Down_MW")
            # Generators that can provide downward regulation
            if int(row[find_list_item_position(headers, "regulation_down")[0]]
                   ):
                d.footroom_variables[generator].append(
                    "Provide_Regulation_Down_MW")

    # TODO: ugly; make this more uniform with the above rather
    # than having two separate methods
    # Get the operational type of each generator
    dynamic_components = \
        read_csv(os.path.join(scenario_directory, "inputs", "generators.tab"),
                 sep="\t", usecols=["GENERATORS", "operational_type"]
                 )

    # Required modules are the unique set of generator operational types
    # This list will be used to know which operational modules to load
    d.required_operational_modules = \
        dynamic_components.operational_type.unique()


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # TODO: figure out how to flag which generators get this variable
    # Generators that can vary power output
    m.Provide_Power_MW = Var(m.DISPATCHABLE_GENERATORS,
                             m.TIMEPOINTS,
                             within=NonNegativeReals)

    # Headroom and footroom services
    m.Provide_LF_Reserves_Up_MW = Var(
        m.LF_RESERVES_UP_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals)
    m.Provide_Regulation_Up_MW = Var(
        m.REGULATION_UP_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals)
    m.Provide_LF_Reserves_Down_MW = Var(
        m.LF_RESERVES_DOWN_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals)
    m.Provide_Regulation_Down_MW = Var(
        m.REGULATION_DOWN_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals)

    # Aggregate the headroom and footroom decision variables respectively for
    # use by the operationa modules
    def headroom_provision_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp] for c in d.headroom_variables[g])
    m.Headroom_Provision_MW = Expression(m.GENERATOR_OPERATIONAL_TIMEPOINTS,
                                         rule=headroom_provision_rule)

    def footroom_provision_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp] for c in d.footroom_variables[g])
    m.Footroom_Provision_MW = Expression(m.GENERATOR_OPERATIONAL_TIMEPOINTS,
                                         rule=footroom_provision_rule)

    # From here, the operational modules determine how the model components are
    # formulated
    m.required_operational_modules = d.required_operational_modules
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_modules(m.required_operational_modules)

    # First, add any components specific to the operational modules
    for op_m in m.required_operational_modules:
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, scenario_directory)

    # Then define operational constraints for all generators
    # Get rules from the generator's operational module
    def power_provision_rule(mod, g, tmp):
        """
        Power provision is a variable for some generators, but not others; get
        the appropriate expression for each generator based on its operational
        type.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            power_provision_rule(mod, g, tmp)
    m.Power_Provision_MW = Expression(m.GENERATOR_OPERATIONAL_TIMEPOINTS,
                                      rule=power_provision_rule)

    def max_power_rule(mod, g, tmp):
        """
        The maximum power and headroom services from a generator; get the
        appropriate variables to be constrained from the generator's
        operational module.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            max_power_rule(mod, g, tmp)
    m.Max_Power_Constraint = Constraint(m.GENERATOR_OPERATIONAL_TIMEPOINTS,
                                        rule=max_power_rule)

    def min_power_rule(mod, g, tmp):
        """
        The minimum amount of power a generator must provide in a timepoint; if
        providing footroom services add those to the minimum level; get the
        appropriate variables to be constrained from the generator's
        operational module.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            min_power_rule(mod, g, tmp)
    m.Min_Power_Constraint = Constraint(m.GENERATOR_OPERATIONAL_TIMEPOINTS,
                                        rule=min_power_rule)

    def fuel_use_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            fuel_use_rule(mod, g, tmp)
    # Fuel use
    m.Fuel_Use_MMBtu = Expression(m.FUEL_GENERATOR_OPERATIONAL_TIMEPOINTS,
                                  rule=fuel_use_rule)

    def startup_rule(mod, g, tmp):
        """
        Track units started up from timepoint to timepoint; get appropriate
        expression from the generator's operational module.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            startup_rule(mod, g, tmp)
    m.Startup_Expression = Expression(
        m.STARTUP_COST_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=startup_rule)

    def shutdown_rule(mod, g, tmp):
        """
        Track units shut down from timepoint to timepoint; get appropriate
        expression from the generator's operational module.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            shutdown_rule(mod, g, tmp)
    m.Shutdown_Expression = Expression(
        m.SHUTDOWN_COST_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_rule)

    # Add generation to load balance
    def total_generation_rule(mod, z, tmp):
        return sum(mod.Power_Provision_MW[g, tmp]
                   for g in mod.OPERATIONAL_GENERATORS_IN_TIMEPOINT[tmp]
                   if mod.load_zone[g] == z)
    m.Generation_in_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                         rule=total_generation_rule)
    d.load_balance_production_components.append("Generation_in_Zone_MW")


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    """
    Traverse required operational modules and load any module-specific data.
    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    imported_operational_modules = \
        load_operational_modules(m.required_operational_modules)
    for op_m in m.required_operational_modules:
        if hasattr(imported_operational_modules[op_m],
                   "load_module_specific_data"):
            imported_operational_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass


def export_results(scenario_directory, horizon, stage, m):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :return:
    """

    m.module_specific_df = []

    imported_operational_modules = \
        load_operational_modules(m.required_operational_modules)
    for op_m in m.required_operational_modules:
        if hasattr(imported_operational_modules[op_m],
                   "export_module_specific_results"):
            imported_operational_modules[op_m].export_module_specific_results(
                m)
        else:
            pass

    # Make pandas dataframes for the various operations variables results
    power_df = make_gen_tmp_var_df(
        m,
        "GENERATOR_OPERATIONAL_TIMEPOINTS",
        "Power_Provision_MW",
        "power_mw")
    lf_reserves_up_df = make_gen_tmp_var_df(
        m,
        "LF_RESERVES_UP_GENERATOR_OPERATIONAL_TIMEPOINTS",
        "Provide_LF_Reserves_Up_MW",
        "lf_reserves_up_mw")
    lf_reserves_down_df = make_gen_tmp_var_df(
        m,
        "LF_RESERVES_DOWN_GENERATOR_OPERATIONAL_TIMEPOINTS",
        "Provide_LF_Reserves_Down_MW",
        "lf_reserves_down_mw")
    regulation_up_df = make_gen_tmp_var_df(
        m,
        "REGULATION_UP_GENERATOR_OPERATIONAL_TIMEPOINTS",
        "Provide_Regulation_Up_MW",
        "regulation_up_mw")
    regulation_down_df = make_gen_tmp_var_df(
        m,
        "REGULATION_DOWN_GENERATOR_OPERATIONAL_TIMEPOINTS",
        "Provide_Regulation_Down_MW",
        "regulation_down_mw")

    dfs_to_merge = [power_df] + m.module_specific_df + \
                   [lf_reserves_up_df, lf_reserves_down_df,
                    regulation_up_df, regulation_down_df]

    df_for_export = reduce(lambda left, right:
                           left.join(right, how="outer"),
                           dfs_to_merge)
    df_for_export.to_csv(
        os.path.join(scenario_directory, horizon, stage, "results",
                     "operations.csv"),
        header=True, index=True)
