#!/usr/bin/env python
import os

from pyomo.environ import *


def add_model_components(m):
    
    # TODO: make this generators in the zone only when multiple zones actually
    # are implemented
    def total_generation_power_rule(m, z, tmp):
        return sum(m.Power_Provision[g, tmp] for g in m.GENERATORS)
    m.Generation_Power = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                    rule=total_generation_power_rule)

    m.energy_generation_components.append("Generation_Power")

    # Add cost to objective function
    # TODO: fix this when periods added, etc.
    def generation_cost_rule(m):
        """
        Power production cost for all generators across all timepoints
        :param m:
        :return:
        """
        return sum(m.Power_Provision[g, tmp] * m.variable_cost[g]
                   for g in m.GENERATORS for tmp in m.TIMEPOINTS)

    m.Total_Generation_Cost = Expression(rule=generation_cost_rule)

    m.total_cost_components.append("Total_Generation_Cost")

    # Penalty variables
    m.Overgeneration = Var(m.LOAD_ZONES, m.TIMEPOINTS, within=NonNegativeReals)
    m.Unserved_Energy = Var(m.LOAD_ZONES, m.TIMEPOINTS, within=NonNegativeReals)

    # TODO: load from file
    m.overgeneration_penalty = Param(initialize=99999999)
    m.unserved_energy_penalty = Param(initialize=99999999)

    m.energy_generation_components.append("Unserved_Energy")
    m.energy_consumption_components.append("Overgeneration")

    # TODO: figure out which module adds this to the load balance
    # 'energy generation' components
    m.load_mw = Param(m.LOAD_ZONES, m.TIMEPOINTS, within=NonNegativeReals)
    m.energy_consumption_components.append("load_mw")

    def total_energy_generation_rule(m, z, tmp):
        """
        Sum across all energy generation components added by other modules for
        each zone and timepoint.
        :param m:
        :param z:
        :param tmp:
        :return:
        """
        return sum(getattr(m, component)[z, tmp]
                   for component in m.energy_generation_components)
    m.Total_Energy_Generation = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                           rule=total_energy_generation_rule)

    def total_energy_consumption_rule(m, z, tmp):
        """
        Sum across all energy consumption components added by other modules
        for each zone and timepoint.
        :param m:
        :param z:
        :param tmp:
        :return:
        """
        return sum(getattr(m, component)[z, tmp]
                   for component in m.energy_consumption_components)
    m.Total_Energy_Consumption = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                            rule=total_energy_consumption_rule)

    def meet_load_rule(m, z, tmp):
        return m.Total_Energy_Generation[z, tmp] \
               == m.Total_Energy_Consumption[z, tmp]

    m.Meet_Load_Constraint = Constraint(m.LOAD_ZONES, m.TIMEPOINTS,
                                        rule=meet_load_rule)

    def penalty_costs_rule(m):
        return sum((m.Unserved_Energy[z, tmp] * m.unserved_energy_penalty +
                    m.Overgeneration[z, tmp] * m.overgeneration_penalty)
                   for z in m.LOAD_ZONES for tmp in m.TIMEPOINTS)
    m.Penalty_Costs = Expression(rule=penalty_costs_rule)
    m.total_cost_components.append("Penalty_Costs")


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "load_mw.tab"),
                     param=m.load_mw
                     )


def export_results(m):
    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Overgeneration[" + str(z) + ", " + str(tmp) + "]: "
                  + str(m.Overgeneration[z, tmp].value)
                  )

    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Unserved_Energy[" + str(z) + ", " + str(tmp) + "]: "
                  + str(m.Unserved_Energy[z, tmp].value)
                  )
