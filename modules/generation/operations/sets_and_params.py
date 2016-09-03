#!/usr/bin/env python

"""
Describe the services that the generation infrastructure can provide, e.g.
power, reserves, ancillary services, etc.
"""
import os.path
from pandas import read_csv

from pyomo.environ import Param, Set, PercentFraction, Boolean, \
    NonNegativeReals,  PositiveReals, BuildAction


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # ### Params defined for all generators ### #
    # Variable O&M cost
    m.variable_om_cost_per_mwh = Param(m.GENERATORS, within=NonNegativeReals)

    # These params will be used to initialize subsets

    # Operational type
    m.operational_type = Param(m.GENERATORS)

    # Headroom services flags
    m.lf_reserves_up = Param(m.GENERATORS, within=Boolean)
    m.regulation_up = Param(m.GENERATORS, within=Boolean)

    # Footroom services flags
    m.lf_reserves_down = Param(m.GENERATORS, within=Boolean)
    m.regulation_down = Param(m.GENERATORS, within=Boolean)

    # Subsets of generators by operational type
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

    m.COMMIT_GENERATORS = Set(initialize=
                              m.DISPATCHABLE_BINARY_COMMIT_GENERATORS |
                              m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS)

    # TODO: this should be built below with the dynamic components
    m.DISPATCHABLE_GENERATORS = Set(initialize=
                                    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS |
                                    m.DISPATCHABLE_NO_COMMIT_GENERATORS |
                                    m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS)
    m.min_stable_level_fraction = Param(m.DISPATCHABLE_GENERATORS,
                                        within=PercentFraction)

    # Subsets of generators by services they can provide
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

    # The components below will be initialized via Pyomo's BuildAction function
    # See:
    # software.sandia.gov/downloads/pub/pyomo/PyomoOnlineDocs.html#BuildAction

    def determine_startup_cost_generators(mod):
        """
        If numeric values greater than 0 for startup costs are specified
        for some generators, add those generators to the
        STARTUP_COST_GENERATORS subset and initialize the respective startup
        cost param value
        :param mod:
        :return:
        """
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS",
                                   "startup_cost"]
                )
        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["startup_cost"]):
            if is_number(row[1]) and float(row[1]) > 0:
                mod.STARTUP_COST_GENERATORS.add(row[0])
                mod.startup_cost_per_unit[row[0]] = float(row[1])
            else:
                pass

    # Generators that incur startup/shutdown costs
    m.STARTUP_COST_GENERATORS = Set(within=m.GENERATORS, initialize=[])
    m.startup_cost_per_unit = Param(m.STARTUP_COST_GENERATORS,
                                    within=PositiveReals, mutable=True,
                                    initialize={})
    m.StartupCostGeneratorsBuild = BuildAction(
        rule=determine_startup_cost_generators)

    def determine_shutdown_cost_generators(mod):
        """
        If numeric values greater than 0 for shutdown costs are specified
        for some generators, add those generators to the
        SHUTDOWON_COST_GENERATORS subset and initialize the respective shutdown
        cost param value
        :param mod:
        :return:
        """
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS",
                                   "shutdown_cost"]
                )
        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["shutdown_cost"]):
            if is_number(row[1]) and float(row[1]) > 0:
                mod.SHUTDOWN_COST_GENERATORS.add(row[0])
                mod.shutdown_cost_per_unit[row[0]] = float(row[1])
            else:
                pass

    m.SHUTDOWN_COST_GENERATORS = Set(within=m.GENERATORS, initialize=[])
    m.shutdown_cost_per_unit = Param(m.SHUTDOWN_COST_GENERATORS,
                                     within=PositiveReals, mutable=True,
                                     initialize={})
    m.ShutdownCostGeneratorsBuild = BuildAction(
        rule=determine_shutdown_cost_generators)

    # TODO: implement check for which generator types can have fuels
    # Fuels and heat rates
    def determine_fuel_generators(mod):
        """
        E.g. generators that use coal, gas, uranium
        :param mod:
        :return:
        """
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS",
                                   "fuel",
                                   "minimum_input_mmbtu_per_hr",
                                   "inc_heat_rate_mmbtu_per_mwh"]
                )

        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["fuel"],
                       dynamic_components["minimum_input_mmbtu_per_hr"],
                       dynamic_components["inc_heat_rate_mmbtu_per_mwh"]):
            if row[1] != ".":
                mod.FUEL_GENERATORS.add(row[0])
                mod.fuel[row[0]] = row[1]
                mod.minimum_input_mmbtu_per_hr[row[0]] = float(row[2])
                mod.inc_heat_rate_mmbtu_per_mwh[row[0]] = float(row[3])
            else:
                pass

    m.FUEL_GENERATORS = Set(within=m.GENERATORS, initialize=[])
    m.fuel = Param(m.FUEL_GENERATORS, within=m.FUELS, mutable=True,
                   initialize={})
    m.minimum_input_mmbtu_per_hr = Param(m.FUEL_GENERATORS, mutable=True,
                                         initialize={})

    m.inc_heat_rate_mmbtu_per_mwh = Param(m.FUEL_GENERATORS, mutable=True,
                                          initialize={})
    m.FuelGeneratorsBuild = BuildAction(rule=determine_fuel_generators)

    # Sets over which we'll define variables
    m.MUST_RUN_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.MUST_RUN_GENERATORS))

    m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.VARIABLE_GENERATORS))

    m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_NO_COMMIT_GENERATORS))

    m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS))

    m.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_CONTINUOUS_COMMIT_GENERATORS))

    m.LF_RESERVES_UP_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.LF_RESERVES_UP_GENERATORS))

    m.LF_RESERVES_DOWN_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.LF_RESERVES_DOWN_GENERATORS))

    m.REGULATION_UP_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.REGULATION_UP_GENERATORS))

    m.REGULATION_DOWN_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.REGULATION_DOWN_GENERATORS))

    m.FUEL_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.FUEL_GENERATORS))

    m.STARTUP_COST_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.STARTUP_COST_GENERATORS))

    m.SHUTDOWN_COST_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.SHUTDOWN_COST_GENERATORS))


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "generators.tab"),
                     index=m.GENERATORS,
                     select=("GENERATORS", "operational_type",
                             "lf_reserves_up", "regulation_up",
                             "lf_reserves_down", "regulation_down",
                             "min_stable_level_fraction",
                             "variable_om_cost_per_mwh"),
                     param=(m.operational_type,
                            m.lf_reserves_up, m.regulation_up,
                            m.lf_reserves_down, m.regulation_down,
                            m.min_stable_level_fraction,
                            m.variable_om_cost_per_mwh)
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
