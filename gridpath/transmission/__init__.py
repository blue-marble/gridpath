#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.transmission** package adds transmission-line-level
components to the model formulation.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param

from gridpath.auxiliary.dynamic_components import required_tx_capacity_modules,\
    required_tx_operational_modules


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """

    :param d:
    :param scenario_directory:
    :param stage:
    :param stage:
    :return:
    """

    # Get the capacity type of each generator
    dynamic_components = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "transmission_lines.tab"),
        sep="\t",
        usecols=["TRANSMISSION_LINES", "tx_capacity_type",
                 "tx_operational_type"]
    )

    # Required capacity modules are the unique set of tx capacity types
    # This list will be used to know which capacity modules to load
    setattr(d, required_tx_capacity_modules,
            dynamic_components.tx_capacity_type.unique()
            )

    # Required operational modules are the unique set of tx operational types
    # This list will be used to know which operational modules to load
    setattr(d, required_tx_operational_modules,
            dynamic_components.tx_operational_type.unique()
            )


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.TRANSMISSION_LINES = Set()
    m.tx_capacity_type = Param(m.TRANSMISSION_LINES)
    m.tx_operational_type = Param(m.TRANSMISSION_LINES)
    m.load_zone_from = Param(m.TRANSMISSION_LINES)
    m.load_zone_to = Param(m.TRANSMISSION_LINES)

    # Capacity-type modules will populate this list if called
    # List will be used to initialize TRANSMISSION_OPERATIONAL_PERIODS
    m.tx_capacity_type_operational_period_sets = []

    # TODO: do we need this actually?
    #  (I don't think so, but added to be aligned with tx cap types)
    # Operational-type modules will populate this list if called
    # List will be used to initialize TRANSMISSION_OPERATIONAL_TIMEPOINTS
    m.tx_operational_type_operational_timepoint_sets = []


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param stage:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(
                        scenario_directory, subproblem, stage, "inputs",
                        "transmission_lines.tab"),
                     select=("TRANSMISSION_LINES", "tx_capacity_type",
                             "tx_operational_type",
                             "load_zone_from", "load_zone_to"),
                     index=m.TRANSMISSION_LINES,
                     param=(m.tx_capacity_type, m.tx_operational_type,
                            m.load_zone_from, m.load_zone_to)
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    transmission_lines = c.execute(
        """SELECT transmission_line, capacity_type, operational_type,
        load_zone_from, load_zone_to
        FROM inputs_transmission_portfolios
        
        LEFT OUTER JOIN
            (SELECT transmission_line, load_zone_from, load_zone_to
            FROM inputs_transmission_load_zones
            WHERE load_zone_scenario_id = {}
            AND transmission_load_zone_scenario_id = {}) as tx_load_zones
        USING (transmission_line)
        
        INNER JOIN
            (SELECT transmission_line, operational_type
            FROM inputs_transmission_operational_chars
            WHERE transmission_operational_chars_scenario_id = {})
        USING (transmission_line)
        
        WHERE transmission_portfolio_scenario_id = {};""".format(
            subscenarios.LOAD_ZONE_SCENARIO_ID,
            subscenarios.TRANSMISSION_LOAD_ZONE_SCENARIO_ID,
            subscenarios.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
        )
    )

    return transmission_lines


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # transmission_lines = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    transmission_lines.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    transmission_lines = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory, "transmission_lines.tab"),
              "w", newline="") as \
            transmission_lines_tab_file:
        writer = csv.writer(transmission_lines_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["TRANSMISSION_LINES", "tx_capacity_type", "tx_operational_type",
             "load_zone_from", "load_zone_to"]
        )

        for row in transmission_lines:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
