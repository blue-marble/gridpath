#!/usr/bin/env python
import os
import csv

from pyomo.environ import *


def determine_dynamic_components(m, inputs_directory):
    """
    Populate the lists of dynamic components.
    Depending on its operational characteristics, different model components get assigned to different generators.
    :param m:
    :param inputs_directory:
    :return:
    """

    # TODO: make more robust than relying on column order
    with open(os.path.join(inputs_directory, "generators.tab"), "rb") as generation_capacity_file:
        generation_capacity_reader = csv.reader(generation_capacity_file, delimiter="\t")
        generation_capacity_reader.next()  # skip header
        for row in generation_capacity_reader:
            generator = row[0]
            # All generators get the following variables
            m.headroom_variables[generator] = list()
            # Generators that can provide upward reserves
            if row[4] == 1:
                m.headroom_variables[generator].append("Upward_Reserve")
            # Generators that can provide regulation
            if row[5] == 1:
                m.headroom_variables[generator].append("Provide_Regulation")


def add_model_components(m):

    # Operational type flags
    m.baseload = Param(m.GENERATORS, within=Boolean)
    m.reserves_up = Param(m.GENERATORS, within=Boolean)
    m.regulation_up = Param(m.GENERATORS, within=Boolean)

    def operational_type_set_init(operational_type):
        """
        Initialize subsets of generators by operational type based on operational type flags.
        Need to return a function with the model as argument, i.e. 'lambda mod' because we can only iterate over the
        generators after data is loaded; then we can pass the abstract model to the initialization function.
        :param operational_type:
        :return:
        """
        return lambda mod: list(g for g in mod.GENERATORS if getattr(mod, operational_type)[g] == 1)

    # Sets by operational types
    m.BASELOAD_GENERATORS = Set(within=m.GENERATORS, initialize=operational_type_set_init("baseload"))
    m.RESERVE_GENERATORS = Set(within=m.GENERATORS, initialize=operational_type_set_init("reserves_up"))
    m.REGULATION_GENERATORS = Set(within=m.GENERATORS, initialize=operational_type_set_init("regulation_up"))

    # All generators have a power variable for now
    m.Power = Var(m.GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)

    # Variables by operational type
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
    print("...loading generation operations data...")
    data_portal.load(filename=os.path.join(inputs_directory, "generators.tab"),
                     index=m.GENERATORS,
                     select=("GENERATORS", "baseload", "reserves_up", "regulation_up"),
                     param=(m.baseload, m.reserves_up, m.regulation_up)
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
