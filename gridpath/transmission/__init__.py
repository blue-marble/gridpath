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
from gridpath.auxiliary.auxiliary import write_validation_to_database


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    Determine the required transmission capacity types and
    transmission operational types based on the inputs in the
    transmission_lines.tab file, and add this information to the
    dynamic components.

    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Get the capacity and operational type of each transmission line
    df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "transmission_lines.tab"),
        sep="\t",
        usecols=["TRANSMISSION_LINES", "tx_capacity_type",
                 "tx_operational_type"]
    )

    # Required capacity modules are the unique set of tx capacity types
    # This list will be used to know which capacity modules to load
    setattr(d, required_tx_capacity_modules,
            df.tx_capacity_type.unique())

    # Required operational modules are the unique set of tx operational types
    # This list will be used to know which operational modules to load
    setattr(d, required_tx_operational_modules,
            df.tx_operational_type.unique())


def add_model_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_LINES`                                                      |
    |                                                                         |
    | The set of transmission lines to be modeled.                            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`tx_capacity_type`                                              |
    | | *Defined over*: :code:`TX_LINES`                                      |
    |                                                                         |
    | The transmission line's capacity type. This will determine how the      |
    | capacity of the line is modeled, e.g. as a specified number or as a     |
    | decision variable in the optimization.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`tx_operational_type`                                           |
    | | *Defined over*: :code:`TX_LINES`                                      |
    |                                                                         |
    | The transmission line's operational type. This will determine how the   |
    | operations of the line are modeled, e.g. through a simple linear        |
    | transport model or power flow using DC OPF assumptions.                 |
    +-------------------------------------------------------------------------+
    | | :code:`load_zone_from`                                                |
    | | *Defined over*: :code:`TX_LINES`                                      |
    |                                                                         |
    | The transmission line's starting load zone (the power flow can go both  |
    | directions, but each line has a defined direction).                     |
    +-------------------------------------------------------------------------+
    | | :code:`load_zone_to`                                                  |
    | | *Defined over*: :code:`TX_LINES`                                      |
    |                                                                         |
    | The transmission line's ending load zone (the power flow can go both    |
    | directions, but each line has a defined direction).                     |
    +-------------------------------------------------------------------------+


    """

    # Sets
    ###########################################################################

    m.TX_LINES = Set()

    # Required Input Params
    ###########################################################################

    m.tx_capacity_type = Param(m.TX_LINES)
    m.tx_operational_type = Param(m.TX_LINES)
    m.load_zone_from = Param(m.TX_LINES)
    m.load_zone_to = Param(m.TX_LINES)

    # Dynamic Components
    ###########################################################################

    # Capacity-type modules will populate this list if called
    # List will be used to initialize TX_OPR_PRDS
    m.tx_capacity_type_operational_period_sets = []


# Input-Output
###############################################################################

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
                     index=m.TX_LINES,
                     param=(m.tx_capacity_type, m.tx_operational_type,
                            m.load_zone_from, m.load_zone_to)
                     )


# Database
###############################################################################

def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # TODO: we might want to get the reactance in the tx_dcopf
    #  tx_operational_type rather than here (see also comment in project/init)
    c = conn.cursor()
    transmission_lines = c.execute(
        """SELECT transmission_line, capacity_type, operational_type,
        load_zone_from, load_zone_to, reactance_ohms
        FROM inputs_transmission_portfolios
        
        LEFT OUTER JOIN
            (SELECT transmission_line, load_zone_from, load_zone_to
            FROM inputs_transmission_load_zones
            WHERE transmission_load_zone_scenario_id = {}) as tx_load_zones
        USING (transmission_line)
        
        INNER JOIN
            (SELECT transmission_line, operational_type, reactance_ohms
            FROM inputs_transmission_operational_chars
            WHERE transmission_operational_chars_scenario_id = {})
        USING (transmission_line)
        
        WHERE transmission_portfolio_scenario_id = {};""".format(
            subscenarios.TRANSMISSION_LOAD_ZONE_SCENARIO_ID,
            subscenarios.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
        )
    )

    return transmission_lines


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
        writer = csv.writer(transmission_lines_tab_file, delimiter="\t", lineterminator="\n")

        # TODO: remove all_caps for TRANSMISSION_LINES and make columns
        #  same as database
        # Write header
        writer.writerow(
            ["TRANSMISSION_LINES", "tx_capacity_type", "tx_operational_type",
             "load_zone_from", "load_zone_to", "reactance_ohms"]
        )

        for row in transmission_lines:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


# Validation
###############################################################################

def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    validation_results = []

    # Get the transmission inputs
    transmission_lines = get_inputs_from_database(
        subscenarios, subproblem, stage, conn
    )

    # Convert input data into pandas DataFrame
    df = pd.DataFrame(
        data=transmission_lines.fetchall(),
        columns=[s[0] for s in transmission_lines.description]
    )

    # Ensure we're not combining incompatible capacity and operational types
    invalid_combos = c.execute(
        """SELECT capacity_type, operational_type 
        FROM mod_tx_capacity_and_tx_operational_type_invalid_combos"""
    ).fetchall()
    validation_errors = validate_op_cap_combos(df, invalid_combos)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "TRANSMISSION_OPERATIONAL_CHARS, TRANSMISSION_PORTFOLIOS",
             "inputs_transmission_operational_chars, inputs_tranmission_portfolios",
             "High",
             "Invalid combination of capacity type and operational type",
             error
             )
        )

    # Check reactance > 0
    validation_errors = validate_reactance(df)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "TRANSMISSION_OPERATIONAL_CHARS",
             "inputs_transmission_operational_chars",
             "High",
             "Invalid reactance inputs",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)


def validate_op_cap_combos(df, invalid_combos):
    """
    Check that there's no mixing of incompatible capacity and operational types
    :param df:
    :param invalid_combos:
    :return:
    """
    results = []
    for combo in invalid_combos:
        bad_combos = ((df["capacity_type"] == combo[0]) &
                      (df["operational_type"] == combo[1]))
        if bad_combos.any():
            bad_lines = df['transmission_line'][bad_combos].values
            print_bad_lines = ", ".join(bad_lines)
            results.append(
                "Line(s) '{}': '{}' and '{}'"
                .format(print_bad_lines, combo[0], combo[1])
            )

    return results


def validate_reactance(df):
    """
    Check reactance > 1 for tx_dcopf lines
    :param df:
    :return:
    """
    results = []

    # df = df[df["operational_type"] == "tx_dcopf"]
    invalids = (df["reactance_ohms"] <= 0)
    if invalids.any():
        bad_lines = df["transmission_line"][invalids].values
        print_bad_lines = ", ".join(bad_lines)
        results.append(
            "Line(s) '{}': expected reactance_ohms > 0"
            .format(print_bad_lines)
        )

    return results
