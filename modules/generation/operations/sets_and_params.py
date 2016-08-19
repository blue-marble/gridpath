#!/usr/bin/env python

"""
Describe the services that the generation infrastructure can provide, e.g.
power, reserves, ancillary services, etc.
"""
import os
import csv
import pandas

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
    dynamic_components = \
        pandas.read_csv(os.path.join(inputs_directory, "generators.tab"),
                        sep="\t", usecols=["GENERATORS",
                                           "startup_cost",
                                           "shutdown_cost"]
                        )

    # If numeric values greater than for startup/shutdown costs are specified
    # for some generators, add those generators to lists that will be used to
    # initialize generators subsets for which startup/shutdown costs will be
    # tracked as well as dictionaries that will be used to initialize the
    # startup_cost and shutdown_cost params
    m.startup_cost_generators = list()  # to init STARTUP_COST_GENERATORS set
    m.startup_cost_by_generator = dict()  # to init startup_cost param
    for row in zip(dynamic_components["GENERATORS"],
                   dynamic_components["startup_cost"]):
        if is_number(row[1]) and float(row[1]) > 0:
            m.startup_cost_generators.append(row[0])
            m.startup_cost_by_generator[row[0]] = float(row[1])
        else:
            pass

    m.shutdown_cost_generators = list()  # to init SHUTDOWN_COST_GENERATORS set
    m.shutdown_cost_by_generator = dict()  # to init shutdown_cost param
    for row in zip(dynamic_components["GENERATORS"],
                   dynamic_components["shutdown_cost"]):
        if is_number(row[1]) and float(row[1]) > 0:
            m.shutdown_cost_generators.append(row[0])
            m.shutdown_cost_by_generator[row[0]] = float(row[1])
        else:
            pass


def add_model_components(m):
    """

    :param m:
    :return:
    """

    m.operational_type = Param(m.GENERATORS)
    m.MUST_RUN_GENERATORS = Set(within=m.GENERATORS,
                                initialize=generator_subset_init(
                                    "operational_type", "must_run")
                                )

    m.VARIABLE_GENERATORS = Set(within=m.GENERATORS,
                                initialize=generator_subset_init(
                                    "operational_type", "variable")
                                )

    m.DISPATCHABLE_NO_COMMIT_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=
        generator_subset_init("operational_type", "dispatchable_no_commit")
        )

    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=
        generator_subset_init("operational_type", "dispatchable_binary_commit")
        )

    m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=
        generator_subset_init("operational_type",
                              "dispatchable_continuous_commit")
        )

    m.DISPATCHABLE_GENERATORS = Set(initialize=
                                    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS |
                                    m.DISPATCHABLE_NO_COMMIT_GENERATORS |
                                    m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS)

    m.min_stable_level = Param(m.DISPATCHABLE_GENERATORS,
                               within=PercentFraction)

    # Headroom services flags
    m.lf_reserves_up = Param(m.GENERATORS, within=Boolean)
    m.regulation_up = Param(m.GENERATORS, within=Boolean)

    # Footroom services flags
    m.lf_reserves_down = Param(m.GENERATORS, within=Boolean)
    m.regulation_down = Param(m.GENERATORS, within=Boolean)

    # Sets of generators that can provide headroom services
    m.LF_RESERVES_UP_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=generator_subset_init("lf_reserves_up", 1))
    m.REGULATION_UP_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=generator_subset_init("regulation_up", 1))

    # Sets of generators that can provide footroom services
    m.LF_RESERVES_DOWN_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=generator_subset_init("lf_reserves_down", 1))
    m.REGULATION_DOWN_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=generator_subset_init("regulation_down", 1))

    # Generatos that incur startup/shutdown costs
    m.STARTUP_COST_GENERATORS = Set(within=m.GENERATORS,
                                    initialize=m.startup_cost_generators)
    m.SHUTDOWN_COST_GENERATORS = Set(within=m.GENERATORS,
                                     initialize=m.shutdown_cost_generators)
    # Startup and shutdown cost (per unit started/shut down)
    m.startup_cost = Param(m.STARTUP_COST_GENERATORS, within=PositiveReals,
                           initialize=m.startup_cost_by_generator)
    m.shutdown_cost = Param(m.SHUTDOWN_COST_GENERATORS, within=PositiveReals,
                            initialize=m.shutdown_cost_by_generator)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "generators.tab"),
                     index=m.GENERATORS,
                     select=("GENERATORS", "operational_type",
                             "lf_reserves_up", "regulation_up",
                             "lf_reserves_down", "regulation_down",
                             "min_stable_level"),
                     param=(m.operational_type,
                            m.lf_reserves_up, m.regulation_up,
                            m.lf_reserves_down, m.regulation_down,
                            m.min_stable_level)
                     )


def generator_subset_init(generator_parameter, expected_type):
    """
    Initialize subsets of generators by operational type based on operational
    type flags.
    Need to return a function with the model as argument, i.e. 'lambda mod'
    because we can only iterate over the
    generators after data is loaded; then we can pass the abstract model to the
    initialization function.
    :param generator_parameter:
    :param expected_type:
    :return:
    """
    return lambda mod: \
        list(g for g in mod.GENERATORS if getattr(mod, generator_parameter)[g]
             == expected_type)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
