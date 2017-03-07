#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, Reals


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
                              horizon, stage):
    data_portal.load(filename=
                     os.path.join(
                         scenario_directory, "inputs",
                         "specified_transmission_line_capacities.tab"),
                     select=("transmission_line", "period",
                             "specified_tx_min_mw", "specified_tx_max_mw"),
                     index=m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS,
                     param=(m.specified_tx_min_mw,
                            m.specified_tx_max_mw)
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # specified_transmission_line_capacities.tab
    with open(os.path.join(inputs_directory,
                           "specified_transmission_line_capacities.tab"), "w") \
            as transmission_lines_specified_capacities_tab_file:
        writer = csv.writer(transmission_lines_specified_capacities_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["transmission_line", "period", "specified_tx_min_mw",
             "specified_tx_max_mw"]
        )

        transmission_lines_specified_capacities = c.execute(
            """SELECT transmission_line, period, min_mw, max_mw
            FROM transmission_line_existing_capacity
            WHERE load_zone_scenario_id = {}
            AND transmission_line_scenario_id = {}
            AND period_scenario_id = {}
            AND transmission_line_existing_capacity_scenario_id = {};
            """.format(
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.TRANSMISSION_LINE_SCENARIO_ID,
                subscenarios.PERIOD_SCENARIO_ID,
                subscenarios.TRANSMISSION_LINE_EXISTING_CAPACITY_SCENARIO_ID
            )
        )
        for row in transmission_lines_specified_capacities:
            writer.writerow(row)
