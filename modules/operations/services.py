#!/usr/bin/env python
import os
import csv

from pyomo.environ import *


def determine_dynamic_components(m, inputs_directory):
    """
    Populate the lists of dynamic components, i.e which generators can provide
    which services. Generators that can vary power output will get the
    Provide_Power variable; generators that can provide reserves will get the
    various reserve variables.
    The operational constraints are then built depending on which services a
    generator can provide.
    :param m:
    :param inputs_directory:
    :return:
    """
    # Generator capabilities
    m.headroom_variables = dict()
    m.footroom_variables = dict()

    with open(os.path.join(inputs_directory, "generators.tab"), "rb") \
            as generation_capacity_file:
        generation_capacity_reader = csv.reader(generation_capacity_file,
                                                delimiter="\t")
        headers = generation_capacity_reader.next()
        # Check that columns are not repeated
        check_list_items_are_unique(headers)
        for row in generation_capacity_reader:
            # Get generator name; we have checked that columns names are unique
            # so can expect a single-item list here and get 0th element
            generator = row[find_list_item_position(headers, "GENERATORS")[0]]
            # All generators get the following variables
            m.headroom_variables[generator] = list()
            m.footroom_variables[generator] = list()
            # In addition, some generators get the variables associated with
            # provision of other services (e.g. reserves) if flagged
            # Generators that can provide upward load-following reserves
            if int(row[find_list_item_position(headers,
                                               "lf_reserves_up")[0]]
                   ):
                m.headroom_variables[generator].append(
                    "Provide_LF_Reserves_Up")
            # Generators that can provide upward regulation
            if int(row[find_list_item_position(headers, "regulation_up")[0]]
                   ):
                m.headroom_variables[generator].append(
                    "Provide_Regulation_Up")
            # Generators that can provide downward load-following reserves
            if int(row[find_list_item_position(headers, "lf_reserves_down")[0]]
                   ):
                m.footroom_variables[generator].append(
                    "Provide_LF_Reserves_Down")
            # Generators that can provide downward regulation
            if int(row[find_list_item_position(headers, "regulation_down")[0]]
                   ):
                m.footroom_variables[generator].append(
                    "Provide_Regulation_Down")


def add_model_components(m):
    """

    :param m:
    :return:
    """

    # TODO: add data check ensuring only a one operational type is assigned to
    # each generator
    # The variables above will be constrained differently depending on
    # generator types
    m.must_run = Param(m.GENERATORS, within=Boolean)
    m.MUST_RUN_GENERATORS = Set(within=m.GENERATORS,
                                initialize=operational_type_set_init(
                                    "must_run")
                                )

    m.variable = Param(m.GENERATORS, within=Boolean)
    m.VARIABLE_GENERATORS = Set(within=m.GENERATORS,
                                initialize=operational_type_set_init(
                                    "variable")
                                )

    m.dispatchable = Param(m.GENERATORS, within=Boolean)
    m.DISPATCHABLE_GENERATORS = Set(within=m.GENERATORS,
                                     initialize=operational_type_set_init(
                                         "dispatchable")
                                     )

    # TODO: figure out how to flag which generators get this variable
    # Generators that can vary power output
    m.Provide_Power = Var(m.DISPATCHABLE_GENERATORS, m.TIMEPOINTS,
                          within=NonNegativeReals)

    # Headroom services flags
    m.lf_reserves_up = Param(m.GENERATORS, within=Boolean)
    m.regulation_up = Param(m.GENERATORS, within=Boolean)

    # Footroom services flags
    m.lf_reserves_down = Param(m.GENERATORS, within=Boolean)
    m.regulation_down = Param(m.GENERATORS, within=Boolean)

    # Sets of generators that can provide headroom services
    m.LF_RESERVES_UP_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=operational_type_set_init("lf_reserves_up"))
    m.REGULATION_UP_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=operational_type_set_init("regulation_up"))

    # Sets of generators that can provide footroom services
    m.LF_RESERVES_DOWN_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=operational_type_set_init("lf_reserves_down"))
    m.REGULATION_DOWN_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=operational_type_set_init("regulation_down"))

    # Headroom and footroom services
    m.Provide_LF_Reserves_Up = Var(m.LF_RESERVES_UP_GENERATORS, m.TIMEPOINTS,
                                   within=NonNegativeReals)
    m.Provide_Regulation_Up = Var(m.REGULATION_UP_GENERATORS, m.TIMEPOINTS,
                                  within=NonNegativeReals)
    m.Provide_LF_Reserves_Down = Var(m.LF_RESERVES_DOWN_GENERATORS,
                                     m.TIMEPOINTS,
                                     within=NonNegativeReals)
    m.Provide_Regulation_Down = Var(m.REGULATION_DOWN_GENERATORS, m.TIMEPOINTS,
                                    within=NonNegativeReals)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "generators.tab"),
                     index=m.GENERATORS,
                     select=("GENERATORS", "must_run", "variable",
                             "dispatchable",
                             "lf_reserves_up", "regulation_up",
                             "lf_reserves_down", "regulation_down"),
                     param=(m.must_run, m.variable, m.dispatchable,
                            m.lf_reserves_up, m.regulation_up,
                            m.lf_reserves_down, m.regulation_down)
                     )


# TODO: figure out what the best place is to export these results
def export_results(m):
    for g in getattr(m, "GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Power_Provision[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Power_Provision[g, tmp].expr.expr.value)
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


def operational_type_set_init(operational_type):
    """
    Initialize subsets of generators by operational type based on operational
    type flags.
    Need to return a function with the model as argument, i.e. 'lambda mod'
    because we can only iterate over the
    generators after data is loaded; then we can pass the abstract model to the
    initialization function.
    :param operational_type:
    :return:
    """
    return lambda mod: \
        list(g for g in mod.GENERATORS if getattr(mod, operational_type)[g]
             == 1)

def check_list_has_single_item(l, error_msg):
    if len(l) > 1:
        raise ValueError(error_msg)
    else:
        pass


def find_list_item_position(l, item):
    """

    :param l:
    :param item:
    :return:
    """
    return [i for i, element in enumerate(l) if element == item]


def check_list_items_are_unique(l):
    """

    :param l:
    :return:
    """
    for item in l:
        positions = find_list_item_position(l, item)
        check_list_has_single_item(
            l=positions,
            error_msg="Service " + str(item) + " is specified more than once" +
            " in generators.tab.")