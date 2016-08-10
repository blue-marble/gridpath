#!/usr/bin/env python

from pyomo.environ import *


def add_model_components(m):

    # Penalty variables
    m.Upward_Reserve_Violation = Var(m.LOAD_ZONES, m.TIMEPOINTS, within=NonNegativeReals)
    m.upward_reserve_violation_penalty = Param(initialize=99999999)

    m.upward_reserve_components.append("Upward_Reserve_Violation")

    # TODO: figure out which module adds this to the load balance 'energy generation' components
    m.upward_reserve_requirement_mw = Param(m.LOAD_ZONES, m.TIMEPOINTS, initialize={("Zone1", 1): 1, ("Zone1", 2): 2})

    def total_upward_reserve_provision_rule(m, z, tmp):
        """
        Sum across all energy generation components added by other modules for each zone and timepoint.
        :param m:
        :param z:
        :param tmp:
        :return:
        """
        return sum(getattr(m, component)[z, tmp]
                   for component in m.upward_reserve_components)
    m.Total_Upward_Reserve = Expression(m.LOAD_ZONES, m.TIMEPOINTS, rule=total_upward_reserve_provision_rule)


    def meet_upward_reserve_rule(m, z, tmp):
        return m.Total_Upward_Reserve[z, tmp] >= m.upward_reserve_requirement_mw[z, tmp]

    m.Meet_Upward_Reserve_Constraint = Constraint(m.LOAD_ZONES, m.TIMEPOINTS, rule=meet_upward_reserve_rule)

    def penalty_costs_rule(m):
        return sum(m.Upward_Reserve_Violation[z, tmp] * m.upward_reserve_violation_penalty
                   for z in m.LOAD_ZONES for tmp in m.TIMEPOINTS)
    m.Reserve_Penalty_Costs = Expression(rule=penalty_costs_rule)
    m.total_cost_components.append("Reserve_Penalty_Costs")


def export_results(m):
    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Upward_Reserve_Violation[" + str(z) + ", " + str(tmp) + "]: "
                  + str(m.Upward_Reserve_Violation[z, tmp].value)
                  )
