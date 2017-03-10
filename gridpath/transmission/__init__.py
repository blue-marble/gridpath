#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param

from gridpath.auxiliary.dynamic_components import required_tx_capacity_modules


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # Get the capacity type of each generator
    dynamic_components = \
        pd.read_csv(os.path.join(scenario_directory, "inputs",
                                 "transmission_lines.tab"),
                    sep="\t", usecols=["TRANSMISSION_LINES", "tx_capacity_type"]
                    )

    # Required modules are the unique set of generator operational types
    # This list will be used to know which operational modules to load
    setattr(d, required_tx_capacity_modules,
            dynamic_components.tx_capacity_type.unique()
            )


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.TRANSMISSION_LINES = Set()
    m.tx_capacity_type = Param(m.TRANSMISSION_LINES)
    m.load_zone_from = Param(m.TRANSMISSION_LINES)
    m.load_zone_to = Param(m.TRANSMISSION_LINES)

    # Capacity-type modules will populate this list if called
    # List will be used to initialize TRANSMISSION_OPERATIONAL_PERIODS
    m.tx_capacity_type_operational_period_sets = []


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
    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           "transmission_lines.tab"),
                     select=("TRANSMISSION_LINES", "tx_capacity_type",
                             "load_zone_from", "load_zone_to"),
                     index=m.TRANSMISSION_LINES,
                     param=(m.tx_capacity_type,
                            m.load_zone_from, m.load_zone_to)
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    # transmission_lines.tab
    with open(os.path.join(inputs_directory, "transmission_lines.tab"),
              "w") as \
            transmission_lines_tab_file:
        writer = csv.writer(transmission_lines_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["TRANSMISSION_LINES", "tx_capacity_type", "load_zone_from",
             "load_zone_to"]
        )

        transmission_lines = c.execute(
            """SELECT transmission_line, capacity_type,
            load_zone_from, load_zone_to
            FROM inputs_transmission_portfolios
            LEFT OUTER JOIN
            (SELECT transmission_line, load_zone_from, load_zone_to
            FROM inputs_transmission_load_zones
            WHERE load_zone_scenario_id = {}
            AND transmission_load_zone_scenario_id = {}) as tx_load_zones
            USING (transmission_line)
            INNER JOIN
            (SELECT transmission_line
            FROM inputs_transmission_operational_chars
            WHERE transmission_operational_chars_scenario_id = {})
            USING (transmission_line)
            WHERE transmission_portfolio_scenario_id = {};""".format(
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.TRANSMISSION_LOAD_ZONE_SCENARIO_ID,
                subscenarios.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID,
                subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
            )
        ).fetchall()

        for row in transmission_lines:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    # existing_generation_period_params.tab
    # TODO: storage currently excluded by selecting NULL energy capacity values
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
            WHERE timepoint_scenario_id = {}) as relevant_periods
            INNER JOIN
            (SELECT transmission_line, period, min_mw, max_mw
            FROM inputs_transmission_existing_capacity
            WHERE transmission_existing_capacity_scenario_id = {} ) as capacity
            USING (transmission_line, period)
            WHERE transmission_portfolio_scenario_id = {};""".format(
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.TRANSMISSION_EXISTING_CAPACITY_SCENARIO_ID,
                subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
            )
        )
        for row in tx_capacities:
            writer.writerow(row)