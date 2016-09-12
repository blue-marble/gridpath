#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, NonNegativeReals


def add_module_specific_components(m):
    """

    """
    m.HYDRO_SPECIFIED_OPERATIONAL_PERIODS = \
        Set(dimen=2)
    m.HYDRO_SPECIFIED_OPERATIONAL_HORIZONS = \
        Set(dimen=2)

    # Add to list of sets we'll join to get the final
    # GENERATOR_OPERATIONAL_PERIODS set
    m.capacity_type_operational_period_sets.append(
        "HYDRO_SPECIFIED_OPERATIONAL_PERIODS",
    )

    m.hydro_specified_power_capacity_mw = \
        Param(m.HYDRO_SPECIFIED_OPERATIONAL_PERIODS,
              within=NonNegativeReals)

    m.hydro_specified_average_power_mwa = \
        Param(m.HYDRO_SPECIFIED_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_specified_min_power_mw = \
        Param(m.HYDRO_SPECIFIED_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_specified_max_power_mw = \
        Param(m.HYDRO_SPECIFIED_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)


# TODO: does this matter for conventional hydro and what if not?
def capacity_rule(mod, g, p):
    return mod.hydro_specified_power_capacity_mw[g, p]


# TODO: give the option to add an exogenous param here instead of 0
def capacity_cost_rule(mod, g, p):
    """
    Capacity cost for specified capacity generators with no economic retirements
    is 0
    :param mod:
    :return:
    """
    return 0


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "hydro_specified_capacities.tab"),
                     index=
                     m.HYDRO_SPECIFIED_OPERATIONAL_PERIODS,
                     select=("hydro_project", "period",
                             "hydro_specified_power_capacity_mw"),
                     param=m.hydro_specified_power_capacity_mw
                     )

    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "hydro_specified_horizon_params.tab"),
                     index=
                     m.HYDRO_SPECIFIED_OPERATIONAL_HORIZONS,
                     select=("hydro_project", "horizon",
                             "hydro_specified_average_power_mwa",
                             "hydro_specified_min_power_mw",
                             "hydro_specified_max_power_mw"),
                     param=(m.hydro_specified_average_power_mwa,
                            m.hydro_specified_min_power_mw,
                            m.hydro_specified_max_power_mw)
                     )
