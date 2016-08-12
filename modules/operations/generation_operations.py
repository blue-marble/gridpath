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
    # Generator capabilities
    m.headroom_variables = dict()
    m.footroom_variables = dict()

    # TODO: make more robust than relying on column order
    with open(os.path.join(inputs_directory, "generators.tab"), "rb") as generation_capacity_file:
        generation_capacity_reader = csv.reader(generation_capacity_file, delimiter="\t")
        generation_capacity_reader.next()  # skip header
        for row in generation_capacity_reader:
            generator = row[0]
            # All generators get the following variables
            m.headroom_variables[generator] = list()
            m.footroom_variables[generator] = list()
            # Generators that can provide upward load-following reserves
            if row[4] == 1:
                m.headroom_variables[generator].append("Provide_LF_Reserves_Up")
            # Generators that can provide upward regulation
            if row[5] == 1:
                m.headroom_variables[generator].append("Provide_Regulation_Up")
            # Generators that can provide downward load-following reserves
            if row[6] == 1:
                m.headroom_variables[generator].append("Provide_LF_Reserves_Down")
            # Generators that can provide downwar dregulation
            if row[7] == 1:
                m.headroom_variables[generator].append("Provide_Regulation_Down")


def add_model_components(m):
    """

    :param m:
    :return:
    """

    # #### Operational types #### #
    # Operational type flags
    m.baseload = Param(m.GENERATORS, within=Boolean)
    m.variable = Param(m.GENERATORS, within=Boolean)
    m.lf_reserves_up = Param(m.GENERATORS, within=Boolean)
    m.regulation_up = Param(m.GENERATORS, within=Boolean)
    m.lf_reserves_down = Param(m.GENERATORS, within=Boolean)
    m.regulation_down = Param(m.GENERATORS, within=Boolean)

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
    m.VARIABLE_GENERATORS = Set(within=m.GENERATORS, initialize=operational_type_set_init("variable"))
    m.LF_RESERVES_UP_GENERATORS = Set(within=m.GENERATORS, initialize=operational_type_set_init("lf_reserves_up"))
    m.REGULATION_UP_GENERATORS = Set(within=m.GENERATORS, initialize=operational_type_set_init("regulation_up"))
    m.LF_RESERVES_DOWN_GENERATORS = Set(within=m.GENERATORS, initialize=operational_type_set_init("lf_reserves_down"))
    m.REGULATION_DOWN_GENERATORS = Set(within=m.GENERATORS, initialize=operational_type_set_init("regulation_down"))

    # #### Parameters by operational type #### #
    m.cap_factor = Param(m.VARIABLE_GENERATORS, m.TIMEPOINTS, within=PercentFraction)

    # #### Operational variables #### #
    # All generators have a power variable for now
    m.Provide_Power = Var(m.GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)

    # Headroom and footroom are derived variables (expressions) that will be used to limit up and down reserves
    # respectively
    # TODO: Change for variable renewables, hydro, etc.
    def headroom_rule(mod, g, tmp):
        if g in mod.VARIABLE_GENERATORS:
            return mod.capacity[g] * mod.cap_factor[g, tmp] - mod.Provide_Power[g, tmp]
        else:
            return mod.capacity[g] - mod.Provide_Power[g, tmp]
    m.Headroom = Expression(m.GENERATORS, m.TIMEPOINTS, rule=headroom_rule)

    # TODO: change for min stable level
    def footroom_rule(mod, g, tmp):
        return mod.Provide_Power[g, tmp]
    m.Footroom = Expression(m.GENERATORS, m.TIMEPOINTS, rule=footroom_rule)

    # Variables by operational type
    m.Provide_LF_Reserves_Up = Var(m.LF_RESERVES_UP_GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)
    m.Provide_Regulation_Up = Var(m.REGULATION_UP_GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)
    m.Provide_LF_Reserves_Down = Var(m.LF_RESERVES_DOWN_GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)
    m.Provide_Regulation_Down = Var(m.REGULATION_DOWN_GENERATORS, m.TIMEPOINTS, within=NonNegativeReals)


    # #### Operational constraints #### #

    # Power
    # TODO: Change for variable renewables, hydro, etc.
    def max_power_rule(mod, g, tmp):
        if g in mod.BASELOAD_GENERATORS:
            return mod.Provide_Power[g, tmp] \
                   == mod.capacity[g]
        if g in mod.VARIABLE_GENERATORS:
            return mod.Provide_Power[g, tmp] \
                   == mod.capacity[g] * mod.cap_factor[g, tmp]
        else:
            return mod.Provide_Power[g, tmp] \
                    <= mod.capacity[g]
    m.Max_Power_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS, rule=max_power_rule)

    # Up reserves
    def max_headroom_rule(mod, g, tmp):
        """
        Components can include upward reserves, regulation
        :param m:
        :param g:
        :param tmp:
        :return:
        """
        return sum(getattr(mod, component)[g, tmp]
                   for component in mod.headroom_variables[g]) \
            <= mod.Headroom[g, tmp]
    m.Max_Headroom_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS, rule=max_headroom_rule)

    # Down reserves
    def max_footroom_rule(mod, g, tmp):
        """
        Components can include upward reserves, regulation
        :param m:
        :param g:
        :param tmp:
        :return:
        """
        return sum(getattr(mod, component)[g, tmp]
                   for component in mod.footroom_variables[g]) \
            <= mod.Footroom[g, tmp]
    m.Max_Footroom_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS, rule=max_headroom_rule)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "generators.tab"),
                     index=m.GENERATORS,
                     select=("GENERATORS", "baseload", "variable",
                             "lf_reserves_up", "regulation_up", "lf_reserves_down", "regulation_down"),
                     param=(m.baseload, m.variable,
                            m.lf_reserves_up, m.regulation_up, m.lf_reserves_down, m.regulation_down)
                     )

    data_portal.load(filename=os.path.join(inputs_directory, "variable_generator_profiles.tab"),
                     index=(m.VARIABLE_GENERATORS, m.TIMEPOINTS),
                     param=m.cap_factor
                     )


def export_results(m):
    for g in getattr(m, "GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Provide_Power[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Provide_Power[g, tmp].value)
                  )
    for g in getattr(m, "LF_RESERVES_UP_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Provide_LF_Reserves_Up[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Provide_LF_Reserves_Up[g, tmp].value)
                  )

    for g in getattr(m, "REGULATION_UP_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Provide_Regulation_Up[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Provide_Regulation_Up[g, tmp].value)
                  )

    for g in getattr(m, "LF_RESERVES_DOWN_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Provide_LF_Reserves_Down[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Provide_LF_Reserves_Down[g, tmp].value)
                  )

    for g in getattr(m, "REGULATION_DOWN_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Provide_Regulation_Down[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Provide_Regulation_Down[g, tmp].value)
                  )
