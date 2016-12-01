#!/usr/bin/env python

"""
Describe operational constraints on the generation infrastructure.
"""
import os.path
from pyomo.environ import Expression

from modules.auxiliary.dynamic_components import required_operational_modules, \
    load_balance_production_components, required_reserve_modules
from modules.auxiliary.auxiliary import make_project_time_var_df, \
    load_operational_type_modules, load_reserve_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # First, add any components specific to the operational modules
    for op_m in getattr(d, required_operational_modules):
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

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
    m.Power_Provision_MW = Expression(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                      rule=power_provision_rule)

    # Add generation to load balance constraint
    def total_power_production_rule(mod, z, tmp):
        return sum(mod.Power_Provision_MW[g, tmp]
                   for g in mod.OPERATIONAL_PROJECTS_IN_TIMEPOINT[tmp]
                   if mod.load_zone[g] == z)
    m.Power_Production_in_Zone_MW = \
        Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                   rule=total_power_production_rule)
    getattr(d, load_balance_production_components).append(
        "Power_Production_in_Zone_MW")

    # Keep track of curtailment
    def curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            curtailment_rule(mod, g, tmp)

    # TODO: possibly create this only if needed by another module?
    m.Curtailment_MW = Expression(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                  rule=curtailment_rule)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "load_module_specific_data"):
            imported_operational_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """

    # Make pandas dataframes for the various operations variables results

    # First power
    power_df = make_project_time_var_df(
        m,
        "PROJECT_OPERATIONAL_TIMEPOINTS",
        "Power_Provision_MW",
        ["project", "timepoint"],
        "power_mw"
        )

    # Then get results from the various modules
    d.module_specific_df = []

    # From the operational type modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "export_module_specific_results"):
            imported_operational_modules[op_m].\
                export_module_specific_results(m, d)
        else:
            pass

    # From the reserve modules
    imported_reserve_modules = \
        load_reserve_type_modules(getattr(d, required_reserve_modules))
    for r_m in getattr(d, required_reserve_modules):
        if hasattr(imported_reserve_modules[r_m],
                   "export_module_specific_results"):
            imported_reserve_modules[r_m].export_module_specific_results(m, d)
        else:
            pass

    # Join all the dataframes and export results
    dfs_to_join = [power_df] + d.module_specific_df

    df_for_export = reduce(lambda left, right:
                           left.join(right, how="outer"),
                           dfs_to_join)
    df_for_export.to_csv(
        os.path.join(scenario_directory, horizon, stage, "results",
                     "operations.csv"),
        header=True, index=True)
