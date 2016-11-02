#!/usr/bin/env python

"""
Describe operational constraints on the generation infrastructure.
"""
import os.path
from pyomo.environ import Param, Expression, Constraint, NonNegativeReals, \
    PercentFraction

from modules.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables, required_operational_modules, \
    load_balance_production_components, required_reserve_modules
from modules.auxiliary.auxiliary import make_project_time_var_df, \
    load_operational_type_modules, load_reserve_type_modules


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # ### Params defined for all generators ### #
    # Operational type
    m.operational_type = Param(m.PROJECTS)

    # Variable O&M cost
    m.variable_om_cost_per_mwh = Param(m.PROJECTS, within=NonNegativeReals)
    # TODO: this should be built below with the dynamic components
    m.min_stable_level_fraction = Param(m.PROJECTS,
                                        within=PercentFraction)

    # Aggregate the headroom and footroom decision variables added by the
    # reserves modules for use by the operational modules
    def headroom_provision_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp] 
                   for c in getattr(d, headroom_variables)[g])
    m.Headroom_Provision_MW = Expression(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                         rule=headroom_provision_rule)

    def footroom_provision_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp] 
                   for c in getattr(d, footroom_variables)[g])
    m.Footroom_Provision_MW = Expression(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                         rule=footroom_provision_rule)

    # From here, the operational modules determine how the model components are
    # formulated
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # First, add any components specific to the operational modules
    for op_m in getattr(d, required_operational_modules):
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m)

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
    m.Max_Power_Constraint = Constraint(m.PROJECT_OPERATIONAL_TIMEPOINTS,
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
    m.Min_Power_Constraint = Constraint(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                        rule=min_power_rule)

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

    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     index=m.PROJECTS,
                     select=("project", "operational_type",
                             "min_stable_level_fraction",
                             "variable_om_cost_per_mwh"),
                     param=(m.operational_type,
                            m.min_stable_level_fraction,
                            m.variable_om_cost_per_mwh)
                     )

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
