#!/usr/bin/env python

from pyomo.environ import *


def add_model_components(m):

    # Penalty variables
    m.Overgeneration = Var(m.LOAD_ZONES, m.TIMEPOINTS, within=NonNegativeReals)
    m.Unserved_Energy = Var(m.LOAD_ZONES, m.TIMEPOINTS, within=NonNegativeReals)

    m.overgeneration_penalty = Param(initialize=99999999)
    m.unserved_energy_penalty = Param(initialize=99999999)

    m.energy_generation_components.append("Unserved_Energy")
    m.energy_consumption_components.append("Overgeneration")

    # TODO: figure out which module adds this to the load balance 'energy generation' components
    m.load_mw = Param(m.LOAD_ZONES, m.TIMEPOINTS, initialize={("Zone1", 1): 10, ("Zone1", 2): 20})
    m.energy_consumption_components.append("load_mw")

    def total_energy_generation_rule(m, z, tmp):
        """
        Sum across all energy generation components added by other modules for each zone and timepoint.
        :param m:
        :param z:
        :param tmp:
        :return:
        """
        return sum(getattr(m, component)[z, tmp]
                   for component in m.energy_generation_components)
    m.Total_Energy_Generation = Expression(m.LOAD_ZONES, m.TIMEPOINTS, rule=total_energy_generation_rule)

    def total_energy_consumption_rule(m, z, tmp):
        """
        Sum across all energy consumption components added by other modules for each zone and timepoint.
        :param m:
        :param z:
        :param tmp:
        :return:
        """
        return sum(getattr(m, component)[z, tmp]
                   for component in m.energy_consumption_components)
    m.Total_Energy_Consumption = Expression(m.LOAD_ZONES, m.TIMEPOINTS, rule=total_energy_consumption_rule)

    def meet_load_rule(m, z, tmp):
        return m.Total_Energy_Generation[z, tmp] == m.Total_Energy_Consumption[z, tmp]

    m.Meet_Load_Constraint = Constraint(m.LOAD_ZONES, m.TIMEPOINTS, rule=meet_load_rule)

    def penalty_costs_rule(m):
        return sum((m.Unserved_Energy[z, tmp] * m.unserved_energy_penalty +
                    m.Overgeneration[z, tmp] * m.overgeneration_penalty)
                   for z in m.LOAD_ZONES for tmp in m.TIMEPOINTS)
    m.Penalty_Costs = Expression(rule=penalty_costs_rule)
    m.total_cost_components.append("Penalty_Costs")