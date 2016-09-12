#!/usr/bin/env python

"""
Simplest implementation with a MWh target
"""

import os.path
from pandas import read_csv

from pyomo.environ import Set, Param, NonNegativeReals, BuildAction, Constraint


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    m.RPS_ZONE_PERIODS_WITH_RPS = Set(dimen=2)
    m.RPS_ZONES = Set(initialize=lambda mod:
                      set(i[0] for i in mod.RPS_ZONE_PERIODS_WITH_RPS)
                      )
    m.rps_target_mwh = Param(m.RPS_ZONE_PERIODS_WITH_RPS, within=NonNegativeReals)

    def determine_rps_generators_by_contract(mod):
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS",
                                   "rps_zone"]
                )
        print dynamic_components
        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["rps_zone"]):
            if row[1] != ".":
                mod.RPS_PROJECTS_BY_RPS_ZONE[row[1]].add(row[0])
            else:
                pass

    m.RPS_PROJECTS_BY_RPS_ZONE = Set(m.RPS_ZONES, initialize=[])
    m.RPSGeneratorsBuild = \
        BuildAction(rule=determine_rps_generators_by_contract)

    # TODO: multiply by horizon weights when implemented
    # TODO: how to deal with curtailment
    def rps_target_rule(mod, z, p):
        return sum(mod.Power_Provision_MW[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   for g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
                   for tmp in mod.TIMEPOINTS_IN_PERIOD[p]) \
            >= mod.rps_target_mwh[z, p]

    m.RPS_Target_Constraint = Constraint(m.RPS_ZONE_PERIODS_WITH_RPS,
                                         rule=rps_target_rule)


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "rps_targets.tab"),
                     index=m.RPS_ZONE_PERIODS_WITH_RPS,
                     param=m.rps_target_mwh,
                     select=("rps_zone", "period", "rps_target_mwh")
                     )