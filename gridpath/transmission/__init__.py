# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The **gridpath.transmission** package adds transmission-line-level
components to the model formulation.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    get_expected_dtypes,
    get_load_zones,
    validate_dtypes,
    validate_columns,
    validate_values,
    validate_missing_inputs,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
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
    | | *Within*: :code:`["tx_new_lin", "tx_spec"]`                           |
    |                                                                         |
    | The transmission line's capacity type. This will determine how the      |
    | capacity of the line is modeled, e.g. as a specified number or as a     |
    | decision variable in the optimization.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`tx_operational_type`                                           |
    | | *Defined over*: :code:`TX_LINES`                                      |
    | | *Within*: :code:`["tx_dcopf", "tx_simple"]`                           |
    |                                                                         |
    | The transmission line's operational type. This will determine how the   |
    | operations of the line are modeled, e.g. through a simple linear        |
    | transport model or power flow using DC OPF assumptions.                 |
    +-------------------------------------------------------------------------+
    | | :code:`load_zone_from`                                                |
    | | *Defined over*: :code:`TX_LINES`                                      |
    | | *Within*: :code:`LOAD_ZONES`                                          |
    |                                                                         |
    | The transmission line's starting load zone (the power flow can go both  |
    | directions, but each line has a defined direction).                     |
    +-------------------------------------------------------------------------+
    | | :code:`load_zone_to`                                                  |
    | | *Defined over*: :code:`TX_LINES`                                      |
    | | *Within*: :code:`LOAD_ZONES`                                          |
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

    m.tx_capacity_type = Param(m.TX_LINES, within=["tx_new_lin", "tx_spec"])
    m.tx_availability_type = Param(
        m.TX_LINES, within=["exogenous", "exogenous_monthly"]
    )
    m.tx_operational_type = Param(m.TX_LINES, within=["tx_dcopf", "tx_simple"])
    m.load_zone_from = Param(m.TX_LINES, within=m.LOAD_ZONES)
    m.load_zone_to = Param(m.TX_LINES, within=m.LOAD_ZONES)


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
    data_portal.load(
        filename=os.path.join(
            scenario_directory, subproblem, stage, "inputs", "transmission_lines.tab"
        ),
        select=(
            "transmission_line",
            "tx_capacity_type",
            "tx_availability_type",
            "tx_operational_type",
            "load_zone_from",
            "load_zone_to",
        ),
        index=m.TX_LINES,
        param=(
            m.tx_capacity_type,
            m.tx_availability_type,
            m.tx_operational_type,
            m.load_zone_from,
            m.load_zone_to,
        ),
    )


# Database
###############################################################################


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage

    # TODO: we might want to get the reactance in the tx_dcopf
    #  tx_operational_type rather than here (see also comment in project/init)
    c = conn.cursor()
    transmission_lines = c.execute(
        """SELECT transmission_line, capacity_type, 
        availability_type, operational_type,
        load_zone_from, load_zone_to, tx_simple_loss_factor, reactance_ohms
        FROM inputs_transmission_portfolios
        
        LEFT OUTER JOIN
            (SELECT transmission_line, load_zone_from, load_zone_to
            FROM inputs_transmission_load_zones
            WHERE transmission_load_zone_scenario_id = {lz}) as tx_load_zones
        USING (transmission_line)
        
        LEFT OUTER JOIN
            (SELECT transmission_line, availability_type
            FROM inputs_transmission_availability
            WHERE transmission_availability_scenario_id = {avl}) as 
            tx_availability
        USING (transmission_line)
        
        LEFT OUTER JOIN
            (SELECT transmission_line, operational_type, 
            tx_simple_loss_factor, reactance_ohms
            FROM inputs_transmission_operational_chars
            WHERE transmission_operational_chars_scenario_id = {opchar})
        USING (transmission_line)
        
        WHERE transmission_portfolio_scenario_id = {portfolio};""".format(
            lz=subscenarios.TRANSMISSION_LOAD_ZONE_SCENARIO_ID,
            avl=subscenarios.TRANSMISSION_AVAILABILITY_SCENARIO_ID,
            opchar=subscenarios.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID,
            portfolio=subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID,
        )
    )

    # TODO: allow Tx lines with no load zones from and to specified, that are only
    #  used for say, reliability capacity exchanges; they would need a different
    #  operational type (no power transfer); the decisions also won't be made at the
    #  transmission line level, but the capacity will limit the aggregate transfer
    #  between PRM zones, so there won't be flow variables

    return transmission_lines


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    transmission_lines.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    transmission_lines = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "transmission_lines.tab",
        ),
        "w",
        newline="",
    ) as transmission_lines_tab_file:
        writer = csv.writer(
            transmission_lines_tab_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            [
                "transmission_line",
                "tx_capacity_type",
                "tx_availability_type",
                "tx_operational_type",
                "load_zone_from",
                "load_zone_to",
                "tx_simple_loss_factor",
                "reactance_ohms",
            ]
        )

        for row in transmission_lines:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


# Validation
###############################################################################


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()

    # Get the transmission inputs
    transmission_lines = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    # Convert input data into pandas DataFrame
    df = cursor_to_df(transmission_lines)

    # Check data types:
    expected_dtypes = get_expected_dtypes(
        conn,
        [
            "inputs_transmission_portfolios",
            "inputs_transmission_availability",
            "inputs_transmission_load_zones",
            "inputs_transmission_operational_chars",
        ],
    )

    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_portfolios, "
        "inputs_transmission_load_zones, "
        "inputs_transmission_operational_chars",
        severity="High",
        errors=dtype_errors,
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in df.columns if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)

    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_operational_chars",
        severity="High",
        errors=validate_values(df, valid_numeric_columns, min=0),
    )

    # Ensure we're not combining incompatible capacity and operational types
    cols = ["capacity_type", "operational_type"]
    invalid_combos = c.execute(
        """
        SELECT {} FROM mod_tx_capacity_and_tx_operational_type_invalid_combos
        """.format(
            ",".join(cols)
        )
    ).fetchall()
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_operational_chars, inputs_tranmission_portfolios",
        severity="High",
        errors=validate_columns(df, cols, invalids=invalid_combos),
    )

    # Check reactance > 0
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_operational_chars",
        severity="High",
        errors=validate_values(df, ["reactance_ohms"], min=0, strict_min=True),
    )

    # Check that all portfolio tx lines are present in the opchar inputs
    msg = (
        "All tx lines in the portfolio should have an operational type "
        "specified in the inputs_transmission_operational_chars table."
    )
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_operational_chars",
        severity="High",
        errors=validate_missing_inputs(
            df, ["operational_type"], idx_col="transmission_line", msg=msg
        ),
    )

    # Check that all portfolio tx lines are present in the load zone inputs
    msg = (
        "All tx lines in the portfolio should have a load zone from/to "
        "specified in the inputs_transmission_load_zones table."
    )
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_load_zones",
        severity="High",
        errors=validate_missing_inputs(
            df, ["load_zone_from", "load_zone_to"], idx_col="transmission_line", msg=msg
        ),
    )

    # Check that all tx load zones are part of the active load zones
    load_zones = get_load_zones(conn, subscenarios)
    for col in ["load_zone_from", "load_zone_to"]:
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_transmission_load_zones",
            severity="High",
            errors=validate_columns(df, col, valids=load_zones),
        )
