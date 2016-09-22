#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, NonNegativeReals


def add_module_specific_components(m):
    """

    """
    m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS = \
        Set(dimen=2)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    m.capacity_type_operational_period_sets.append(
        "STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS",
    )
    # Add to list of sets we'll join to get the final
    # STORAGE_OPERATIONAL_PERIODS set
    m.storage_only_capacity_type_operational_period_sets.append(
        "STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS",
    )

    m.storage_specified_power_capacity_mw = \
        Param(m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS,
              within=NonNegativeReals)

    m.storage_specified_energy_capacity_mwh = \
        Param(m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS,
              within=NonNegativeReals)


def capacity_rule(mod, g, p):
    return mod.storage_specified_power_capacity_mw[g, p]


def energy_capacity_rule(mod, g, p):
    return mod.storage_specified_energy_capacity_mwh[g, p]


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
                                  "storage_specified_capacities.tab"),
                     index=
                     m.STORAGE_SPECIFIED_NO_ECON_RETRMNT_OPERATIONAL_PERIODS,
                     select=("storage_project", "period",
                             "storage_specified_power_capacity_mw",
                             "storage_specified_energy_capacity_mwh"),
                     param=(m.storage_specified_power_capacity_mw,
                            m.storage_specified_energy_capacity_mwh)
                     )
