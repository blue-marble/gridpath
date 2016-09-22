#!/usr/bin/env python

"""
Simplest implementation with a MWh target
"""

import csv
import os.path
from pandas import read_csv

from pyomo.environ import Set, Param, Expression, NonNegativeReals, \
    BuildAction, Constraint, value


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
    m.rps_target_mwh = Param(m.RPS_ZONE_PERIODS_WITH_RPS,
                             within=NonNegativeReals)

    def determine_rps_generators_by_contract(mod):
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "rps_zone"]
                )
        for row in zip(dynamic_components["project"],
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
    def rps_energy_provision_rule(mod, z, p):
        """
        Calculate the delivered RPS energy for each zone and period
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.Power_Provision_MW[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   for g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
                   for tmp in mod.TIMEPOINTS_IN_PERIOD[p])

    m.Total_Delivered_RPS_Energy_MWh = \
        Expression(m.RPS_ZONE_PERIODS_WITH_RPS,
                   rule=rps_energy_provision_rule)

    def rps_target_rule(mod, z, p):
        """
        Total delivered RPS-eligible energy must exceed target
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return mod.Total_Delivered_RPS_Energy_MWh[z, p] \
            >= mod.rps_target_mwh[z, p]

    m.RPS_Target_Constraint = Constraint(m.RPS_ZONE_PERIODS_WITH_RPS,
                                         rule=rps_target_rule)

    def curtailed_rps_energy_rule(mod, z, p):
        """
        Calculate how much RPS-eligible energy was curtailed in each RPS zone
        in each period
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.Curtailment_MW[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   for g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
                   for tmp in mod.TIMEPOINTS_IN_PERIOD[p])
    # TODO: is this only needed for export and, if so, should it be created on
    # export?
    m.Total_Curtailed_RPS_Energy_MWh = \
        Expression(m.RPS_ZONE_PERIODS_WITH_RPS,
                   rule=curtailed_rps_energy_rule)


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "rps_targets.tab"),
                     index=m.RPS_ZONE_PERIODS_WITH_RPS,
                     param=m.rps_target_mwh,
                     select=("rps_zone", "period", "rps_target_mwh")
                     )


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "rps.csv"), "wb") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["rps_zone", "period", "rps_target_mwh",
                         "delivered_rps_energy_mwh",
                         "curtailed_rps_energy_mwh"])
        for (z, p) in m.RPS_ZONE_PERIODS_WITH_RPS:
            writer.writerow([
                z,
                p,
                m.rps_target_mwh[z, p],
                value(m.Total_Delivered_RPS_Energy_MWh[z, p]),
                value(m.Total_Curtailed_RPS_Energy_MWh[z, p])
            ])


def save_duals(m):
    m.constraint_indices["RPS_Target_Constraint"] = \
        ["rps_zone", "period", "dual"]
