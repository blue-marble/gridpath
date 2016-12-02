#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, Expression

from modules.auxiliary.dynamic_components import required_tx_capacity_modules, \
    total_cost_components
from modules.auxiliary.auxiliary import load_tx_capacity_type_modules, \
    make_project_time_var_df


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed transmission capacity type modules
    imported_tx_capacity_modules = \
        load_tx_capacity_type_modules(getattr(d, required_tx_capacity_modules))
    # First, add any components specific to the transmission capacity modules
    for op_m in getattr(d, required_tx_capacity_modules):
        imp_op_m = imported_tx_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    def join_tx_cap_type_operational_period_sets(mod):
        """
        Join the sets we need to make the TRANSMISSION_OPERATIONAL_PERIODS
        super set; if list contains only a single set, return just that set
        :param mod:
        :return:
        """
        if len(mod.tx_capacity_type_operational_period_sets) == 0:
            return []
        elif len(mod.tx_capacity_type_operational_period_sets) == 1:
            return getattr(mod, mod.tx_capacity_type_operational_period_sets[0])

        else:
            return reduce(lambda x, y: getattr(mod, x) | getattr(mod, y),
                          mod.tx_capacity_type_operational_period_sets)

    m.TRANSMISSION_OPERATIONAL_PERIODS = \
        Set(dimen=2, within=m.TRANSMISSION_LINES*m.PERIODS,
            initialize=join_tx_cap_type_operational_period_sets)

    def transmission_min_capacity_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type]. \
            min_transmission_capacity_rule(mod, tx, p)

    m.Transmission_Min_Capacity_MW = \
        Expression(m.TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=transmission_min_capacity_rule)

    def transmission_max_capacity_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type]. \
            max_transmission_capacity_rule(mod, tx, p)

    m.Transmission_Max_Capacity_MW = \
        Expression(m.TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=transmission_max_capacity_rule)

    # Add costs to objective function
    def tx_capacity_cost_rule(mod, tx, p):
        """
        Get capacity cost from each line's respective capacity module
        :param mod:
        :param g:
        :param p:
        :return:
        """
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type].\
            tx_capacity_cost_rule(mod, tx, p)
    m.Transmission_Capacity_Cost_in_Period = \
        Expression(m.TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=tx_capacity_cost_rule)

    # Add costs to objective function
    def total_tx_capacity_cost_rule(mod):
        return sum(mod.Transmission_Capacity_Cost_in_Period[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for (g, p) in mod.TRANSMISSION_OPERATIONAL_PERIODS)
    m.Total_Tx_Capacity_Costs = Expression(rule=total_tx_capacity_cost_rule)
    getattr(d, total_cost_components).append("Total_Tx_Capacity_Costs")


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
    imported_tx_capacity_modules = \
        load_tx_capacity_type_modules(getattr(d, required_tx_capacity_modules))
    for op_m in getattr(d, required_tx_capacity_modules):
        if hasattr(imported_tx_capacity_modules[op_m],
                   "load_module_specific_data"):
            imported_tx_capacity_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    d.tx_module_specific_df = []

    imported_tx_capacity_modules = \
        load_tx_capacity_type_modules(getattr(d, required_tx_capacity_modules))
    for op_m in getattr(d, required_tx_capacity_modules):
        if hasattr(imported_tx_capacity_modules[op_m],
                   "export_module_specific_results"):
            imported_tx_capacity_modules[op_m].export_module_specific_results(
                m, d)
        else:
            pass

    # Export transmission capacity
    min_cap_df = \
        make_project_time_var_df(
            m,
            "TRANSMISSION_OPERATIONAL_PERIODS",
            "Transmission_Min_Capacity_MW",
            ["transmission_line", "period"],
            "transmission_min_capacity_mw"
        )

    max_cap_df = \
        make_project_time_var_df(
            m,
            "TRANSMISSION_OPERATIONAL_PERIODS",
            "Transmission_Max_Capacity_MW",
            ["transmission_line", "period"],
            "transmission_max_capacity_mw"
        )

    cap_dfs_to_merge = [min_cap_df] + [max_cap_df] + d.tx_module_specific_df
    cap_df_for_export = reduce(lambda left, right:
                               left.join(right, how="outer"),
                               cap_dfs_to_merge)
    cap_df_for_export.to_csv(
        os.path.join(scenario_directory, horizon, stage, "results",
                     "transmission_capacity.csv"),
        header=True, index=True)
