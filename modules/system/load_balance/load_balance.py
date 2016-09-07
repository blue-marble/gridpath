#!/usr/bin/env python

import os.path
from pyomo.environ import Param, Var, Expression, Constraint, NonNegativeReals


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    def total_load_balance_production_rule(mod, z, tmp):
        """
        Sum across all energy generation components added by other modules for
        each zone and timepoint.
        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        return sum(getattr(mod, component)[z, tmp]
                   for component in d.load_balance_production_components)
    m.Total_Energy_Production_MW = Expression(
        m.LOAD_ZONES, m.TIMEPOINTS,
        rule=total_load_balance_production_rule)

    def total_load_balance_consumption_rule(mod, z, tmp):
        """
        Sum across all energy consumption components added by other modules
        for each zone and timepoint.
        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        return sum(getattr(mod, component)[z, tmp]
                   for component in d.load_balance_consumption_components)
    m.Total_Energy_Consumption_MW = Expression(
        m.LOAD_ZONES, m.TIMEPOINTS,
        rule=total_load_balance_consumption_rule)

    def meet_load_rule(mod, z, tmp):
        return mod.Total_Energy_Production_MW[z, tmp] \
               == mod.Total_Energy_Consumption_MW[z, tmp]

    m.Meet_Load_Constraint = Constraint(m.LOAD_ZONES, m.TIMEPOINTS,
                                        rule=meet_load_rule)


def save_duals(m):
    m.constraint_indices["Meet_Load_Constraint"] = \
        ["zone", "timepoint", "dual"]