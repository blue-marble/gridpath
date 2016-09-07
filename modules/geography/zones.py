#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, Var, NonNegativeReals


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    m.LOAD_ZONES = Set()

    # Static load
    m.static_load_mw = Param(m.LOAD_ZONES, m.TIMEPOINTS,
                             within=NonNegativeReals)
    d.load_balance_consumption_components.append("static_load_mw")

    # Penalty variables
    m.Overgeneration_MW = Var(m.LOAD_ZONES, m.TIMEPOINTS,
                              within=NonNegativeReals)
    m.Unserved_Energy_MW = Var(m.LOAD_ZONES, m.TIMEPOINTS,
                               within=NonNegativeReals)

    # TODO: load from file
    m.overgeneration_penalty_per_mw = Param(initialize=99999999)
    m.unserved_energy_penalty_per_mw = Param(initialize=99999999)

    d.load_balance_production_components.append("Unserved_Energy_MW")
    d.load_balance_consumption_components.append("Overgeneration_MW")


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           "load_zones.tab"),
                     set=m.LOAD_ZONES
                     )

    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "load_mw.tab"),
                     param=m.static_load_mw
                     )


def export_results(scenario_directory, horizon, stage, m):
    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Overgeneration_MW[" + str(z) + ", " + str(tmp) + "]: "
                  + str(m.Overgeneration_MW[z, tmp].value)
                  )

    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Unserved_Energy_MW[" + str(z) + ", " + str(tmp) + "]: "
                  + str(m.Unserved_Energy_MW[z, tmp].value)
                  )