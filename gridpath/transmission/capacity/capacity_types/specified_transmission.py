#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, Reals


# TODO: add fixed O&M cost
def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS = Set(dimen=2)
    m.tx_capacity_type_operational_period_sets.append(
        "SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS"
    )

    m.specified_tx_min_mw = \
        Param(m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS, within=Reals)
    m.specified_tx_max_mw = \
        Param(m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS, within=Reals)


def min_transmission_capacity_rule(mod, tx, p):
    return mod.specified_tx_min_mw[tx, p]


def max_transmission_capacity_rule(mod, tx, p):
    return mod.specified_tx_max_mw[tx, p]


# TODO: should there be a fixed cost for keeping transmission around
def tx_capacity_cost_rule(mod, g, p):
    """
    None for now
    :param mod:
    :return:
    """
    return 0


def load_module_specific_data(m, data_portal, scenario_directory,
                              subproblem, stage):
    data_portal.load(filename=
                     os.path.join(scenario_directory, subproblem, stage, "inputs",
                                  "specified_transmission_line_capacities.tab"),
                     select=("transmission_line", "period",
                             "specified_tx_min_mw", "specified_tx_max_mw"),
                     index=m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS,
                     param=(m.specified_tx_min_mw,
                            m.specified_tx_max_mw)
                     )


def get_module_specific_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    specified_transmission_line_capacities.tab
    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    with open(os.path.join(inputs_directory,
                           "specified_transmission_line_capacities.tab"),
              "w") as existing_tx_capacity_tab_file:
        writer = csv.writer(existing_tx_capacity_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["transmission_line", "period", "specified_tx_min_mw",
             "specified_tx_max_mw"]
        )

        tx_capacities = c.execute(
            """SELECT transmission_line, period, min_mw, max_mw
            FROM inputs_transmission_portfolios
            CROSS JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE temporal_scenario_id = {}) as relevant_periods
            INNER JOIN
            (SELECT transmission_line, period, min_mw, max_mw
            FROM inputs_transmission_existing_capacity
            WHERE transmission_existing_capacity_scenario_id = {} ) as capacity
            USING (transmission_line, period)
            WHERE transmission_portfolio_scenario_id = {};""".format(
                subscenarios.TEMPORAL_SCENARIO_ID,
                subscenarios.TRANSMISSION_EXISTING_CAPACITY_SCENARIO_ID,
                subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
            )
        )
        for row in tx_capacities:
            writer.writerow(row)
