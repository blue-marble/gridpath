#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, NonNegativeReals


def add_module_specific_components(m):
    """

    """
    m.specified_capacity_mw = \
        Param(m.SPECIFIED_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
              within=NonNegativeReals)


def capacity_rule(mod, g, p):
    return mod.specified_capacity_mw[g, p]


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
