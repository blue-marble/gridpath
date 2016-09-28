#!/usr/bin/env python

import csv
import os.path
from pyomo.environ import Param, Expression, NonNegativeReals


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    m.overgeneration_penalty_per_mw = \
        Param(m.LOAD_ZONES, within=NonNegativeReals)
    m.unserved_energy_penalty_per_mw = \
        Param(m.LOAD_ZONES, within=NonNegativeReals)

    def penalty_costs_rule(mod):
        return sum((mod.Unserved_Energy_MW[z, tmp]
                    * mod.unserved_energy_penalty_per_mw[z] +
                    mod.Overgeneration_MW[z, tmp]
                    * mod.overgeneration_penalty_per_mw[z])
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for z in mod.LOAD_ZONES for tmp in mod.TIMEPOINTS)
    m.Load_Balance_Penalty_Costs = Expression(rule=penalty_costs_rule)
    d.total_cost_components.append("Load_Balance_Penalty_Costs")


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "load_zones.tab"),
                     param=(m.overgeneration_penalty_per_mw,
                            m.unserved_energy_penalty_per_mw)
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
    pass
    # TODO: export costs
