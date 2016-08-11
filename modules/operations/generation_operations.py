#!/usr/bin/env python
import os
import csv

from pyomo.environ import *


def determine_dynamic_components(m, inputs_directory):
    """
    Populate the lists of dynamic components
    :param m:
    :param inputs_directory:
    :return:
    """
    with open(os.path.join(inputs_directory, "generation_capacity.tab"), "rb") as generation_capacity_file:
        generation_capacity_reader = csv.reader(generation_capacity_file, delimiter="\t")
        generation_capacity_reader.next()  # skip header
        for row in generation_capacity_reader:
            generator = row[0]
            print generator
            m.headroom_variables[generator] = list()

    with open(os.path.join(inputs_directory, "reserve_generators.tab"), "rb") as reserve_generators_file:
        reserve_generators_reader = csv.reader(reserve_generators_file, delimiter="\t")
        reserve_generators_reader.next()  # skip header
        for row in reserve_generators_reader:
            generator = row[0]
            m.headroom_variables[generator].append("Upward_Reserve")

    with open(os.path.join(inputs_directory, "regulation_generators.tab"), "rb") as regulation_generators_file:
        regulation_generators_reader = csv.reader(regulation_generators_file, delimiter="\t")
        regulation_generators_reader.next()  # skip header
        for row in regulation_generators_reader:
            generator = row[0]
            m.headroom_variables[generator].append("Provide_Regulation")


def add_model_components(m):

    # Operational types
    m.RESERVE_GENERATORS = Set(within=m.GENERATORS)
    m.REGULATION_GENERATORS = Set(within=m.GENERATORS)
    m.BASELOAD_GENERATORS = Set(within=m.GENERATORS)

    m.Power = Var(m.GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)

    # Services
    m.Upward_Reserve = Var(m.RESERVE_GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)
    m.Provide_Regulation = Var(m.REGULATION_GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)

    def headroom_rule(m, g, tmp):
        if g in m.BASELOAD_GENERATORS:
            return 0
        else:
            return m.capacity[g] - m.Power[g, tmp]

    m.Headroom = Expression(m.GENERATORS, m.TIMEPOINTS, rule=headroom_rule)
    m.Footroom = Expression(m.GENERATORS, m.TIMEPOINTS)

    def max_power_rule(m, g, tmp):
        return m.Power[g, tmp] + m.Headroom[g, tmp]\
               == m.capacity[g]

    m.Max_Power_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS, rule=max_power_rule)

    def max_headroom_rule(m, g, tmp):
        """
        Components can include upward reserves, regulation
        :param m:
        :param g:
        :param tmp:
        :return:
        """
        return sum(getattr(m, component)[g, tmp]
                   for component in m.headroom_variables[g]) \
            <= m.Headroom[g, tmp]
    m.Max_Headroom_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS, rule=max_headroom_rule)

    # TODO: make this generators in the zone only when multiple zones actually are implemented
    def total_generation_power_rule(m, z, tmp):
        return sum(m.Power[g, tmp] for g in m.GENERATORS)
    m.Generation_Power = Expression(m.LOAD_ZONES, m.TIMEPOINTS, rule=total_generation_power_rule)

    m.energy_generation_components.append("Generation_Power")

    # Add cost to objective function
    # TODO: fix this when periods added, etc.
    def generation_cost_rule(m):
        """
        Power production cost for all generators across all timepoints
        :param m:
        :return:
        """
        return sum(m.Power[g, tmp] * m.variable_cost[g] for g in m.GENERATORS for tmp in m.TIMEPOINTS)

    m.Total_Generation_Cost = Expression(rule=generation_cost_rule)

    m.total_cost_components.append("Total_Generation_Cost")


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "reserve_generators.tab"),
                     set=m.RESERVE_GENERATORS
                     )

    data_portal.load(filename=os.path.join(inputs_directory, "regulation_generators.tab"),
                     set=m.REGULATION_GENERATORS
                     )

    data_portal.load(filename=os.path.join(inputs_directory, "baseload_generators.tab"),
                     set=m.BASELOAD_GENERATORS
                     )

def export_results(m):
    for g in getattr(m, "GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Power[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Power[g, tmp].value)
                  )
    for g in getattr(m, "RESERVE_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Upward_Reserve[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Upward_Reserve[g, tmp].value)
                  )

    for g in getattr(m, "REGULATION_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Regulation[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Provide_Regulation[g, tmp].value)
                  )
