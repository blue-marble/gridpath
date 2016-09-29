#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, NonNegativeReals

from modules.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets

def add_module_specific_components(m, d):
    """

    """
    m.SPECIFIED_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS = \
        Set(dimen=2)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "SPECIFIED_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS",
    )

    m.specified_capacity_mw = \
        Param(m.SPECIFIED_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
              within=NonNegativeReals)


def capacity_rule(mod, g, p):
    return mod.specified_capacity_mw[g, p]


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
                                  "generator_specified_capacities.tab"),
                     index=
                     m.SPECIFIED_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
                     select=("GENERATORS", "PERIODS", "specified_capacity_mw"),
                     param=m.specified_capacity_mw
                     )
