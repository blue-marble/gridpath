# Copyright 2016-2023 Blue Marble Analytics LLC.
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
This operational type describes transmission lines whose flows are simulated
using a linear transport model, i.e. transmission flow is constrained to be
less than or equal to the line capacity. Line capacity can be defined for
both transmission flow directions. The user can define losses as a fraction
of line flow.

"""

import csv
import os
import pandas as pd
from pyomo.environ import (
    Set,
    Param,
    Var,
    Constraint,
    NonNegativeReals,
    Reals,
    PercentFraction,
)

from gridpath.auxiliary.db_interface import directories_to_db_values

Negative_Infinity = float("-inf")
Infinity = float("inf")


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT`                           |
    |                                                                         |
    | Two-dimensional set with transmission lines of the :code:`tx_simple`    |
    | operational type and their operational timepoints to describe all       |
    | possible transmission-timepoint combinations for transmission lines     |
    | with a minimum flow specified. Can include tx_simple and                |
    | tx_simple_binary lines, don't apply to DC power flow.                   |
    +-------------------------------------------------------------------------+
    | | :code:`TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT`                           |
    |                                                                         |
    | Two-dimensional set with transmission lines of the :code:`tx_simple`    |
    | operational type and their operational timepoints to describe all       |
    | possible transmission-timepoint combinations for transmission lines     |
    | with a maximum flow specified. Can include tx_simple and                |
    | tx_simple_binary lines. Don't apply to DC power flow.                   |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Optional Params                                                         |
    +=========================================================================+
    | | :code:`tx_simple_min_flow_mw`                                         |
    | | *Defined over*: :code:`TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT            |
    | | *Within*: :code:`Reals`                                               |
    | | *Default*: :code:`Negative_Infinity`                                  |
    |                                                                         |
    | The minimum flow (in MW) that must be transmitted in a                  |
    | transmission line in each timepoint.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`tx_simple_max_flow_mw`                                         |
    | | *Defined over*: :code:`TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT            |
    | | *Within*: :code:`Reals`                                               |
    | | *Default*: :code:`Infinity`                                           |
    |                                                                         |
    | The maximum flow (in MW) that can be transmitted in a                   |
    | transmission line in each timepoint.                                    |
    +-------------------------------------------------------------------------+


    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`TxSimple_Min_Flow_Constraint`                                  |
    | | *Defined over*: :code:`TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT`           |
    |                                                                         |
    | Transmitted power should exceed the minimum transmitted power in each   |
    | operational timepoint.                                                  |
    +-------------------------------------------------------------------------+
    | | :code:`TxSimple_Max_Flow_Constraint`                                  |
    | | *Defined over*: :code:`TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT`           |
    |                                                                         |
    | Transmitted power should not exceed the maximum transmitted power in    |
    | each operational timepoint.                                             |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT = Set(dimen=2, within=m.TX_OPR_TMPS)

    m.TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT = Set(dimen=2, within=m.TX_OPR_TMPS)

    # Optional Params
    ###########################################################################

    m.tx_simple_min_flow_mw = Param(
        m.TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT, within=Reals, default=Negative_Infinity
    )

    m.tx_simple_max_flow_mw = Param(
        m.TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT, within=Reals, default=Infinity
    )

    # Constraints
    ###########################################################################

    m.TxSimple_Min_Flow_Constraint = Constraint(
        m.TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT, rule=min_flow_rule
    )

    m.TxSimple_Max_Flow_Constraint = Constraint(
        m.TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT, rule=max_flow_rule
    )


# Constraint Formulation Rules
###############################################################################


def min_flow_rule(mod, l, tmp):
    """
    **Constraint Name**: TxSimple_Min_Flow_Constraint
    **Enforced Over**: TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT

    Transmitted power should exceed the defined minimum flow in
    each operational timepoint.
    """
    var = mod.tx_simple_min_flow_mw[l, tmp]
    if var == Negative_Infinity:
        return Constraint.Skip
    else:
        return mod.Transmit_Power_MW[l, tmp] >= var


def max_flow_rule(mod, l, tmp):
    """
    **Constraint Name**: TxSimple_Max_Flow_Constraint
    **Enforced Over**: TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT

    Transmitted power should not exceed the defined maximum flow in
    each operational timepoint.
    """
    var = mod.tx_simple_max_flow_mw[l, tmp]
    if var == Infinity:
        return Constraint.Skip
    else:
        return mod.Transmit_Power_MW[l, tmp] <= var


# Input-Output
###############################################################################


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    transmission_flow_limits_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "transmission_flow_limits.tab",
    )

    if os.path.exists(transmission_flow_limits_file):
        # Min Flow
        transmission_tmps_with_min = list()
        min_flow_mw = dict()

        header = pd.read_csv(
            transmission_flow_limits_file,
            sep="\t",
            header=None,
            nrows=1,
        ).values[0]

        optional_columns = ["min_flow_mw"]
        used_columns = [c for c in optional_columns if c in header]

        df = pd.read_csv(
            transmission_flow_limits_file,
            sep="\t",
            usecols=["transmission_line", "timepoint"] + used_columns,
        )

        # min_flow_mw is optional,
        # so TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT
        # and min_flow_mw simply won't be initialized if
        # min_flow_mw does not exist in the input file
        if "min_flow_mw" in df.columns:
            for row in zip(df["transmission_line"], df["timepoint"], df["min_flow_mw"]):
                if row[2] != ".":
                    transmission_tmps_with_min.append((row[0], row[1]))
                    min_flow_mw[(row[0], row[1])] = float(row[2])
                else:
                    pass

        # Load min flow data
        if not transmission_tmps_with_min:
            pass  # if the list is empty, don't initialize the set
        else:
            data_portal.data()["TX_SIMPLE_OPR_TMPS_W_MIN_CONSTRAINT"] = {
                None: transmission_tmps_with_min
            }

        data_portal.data()["tx_simple_min_flow_mw"] = min_flow_mw

        # Max Flow
        transmission_tmps_with_max = list()
        max_flow_mw = dict()

        header = pd.read_csv(
            transmission_flow_limits_file,
            sep="\t",
            header=None,
            nrows=1,
        ).values[0]

        optional_columns = ["max_flow_mw"]
        used_columns = [c for c in optional_columns if c in header]

        df = pd.read_csv(
            transmission_flow_limits_file,
            sep="\t",
            usecols=["transmission_line", "timepoint"] + used_columns,
        )

        # max_flow_mw is optional,
        # so TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT
        # and max_flow_mw simply won't be initialized if
        # max_flow_mw does not exist in the input file
        if "max_flow_mw" in df.columns:
            for row in zip(df["transmission_line"], df["timepoint"], df["max_flow_mw"]):
                if row[2] != ".":
                    transmission_tmps_with_max.append((row[0], row[1]))
                    max_flow_mw[(row[0], row[1])] = float(row[2])
                else:
                    pass

        # Load max flow data
        if not transmission_tmps_with_max:
            pass  # if the list is empty, don't initialize the set
        else:
            data_portal.data()["TX_SIMPLE_OPR_TMPS_W_MAX_CONSTRAINT"] = {
                None: transmission_tmps_with_max
            }

        data_portal.data()["tx_simple_max_flow_mw"] = max_flow_mw


def get_model_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    tx_flow = c.execute(
        """SELECT transmission_line, timepoint, min_flow_mw, max_flow_mw
        FROM inputs_transmission_flow
        JOIN
        (SELECT timepoint
        FROM inputs_temporal
        WHERE temporal_scenario_id = {}) as relevant_timepoints
        USING (timepoint)        
        JOIN
        (SELECT transmission_line
        FROM inputs_transmission_portfolios
        WHERE transmission_portfolio_scenario_id = {}) as relevant_tx
        USING (transmission_line)
        WHERE transmission_flow_scenario_id = {}
        AND stage_ID = {}
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID,
            subscenarios.TRANSMISSION_FLOW_SCENARIO_ID,
            stage,
        )
    )

    return tx_flow


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
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
    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    tx_flow = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    ).fetchall()

    # Only write tab file if we have data to limit flows
    if len(tx_flow) > 0:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "transmission_flow_limits.tab",
            ),
            "w",
            newline="",
        ) as tx_flow_tab_file:
            writer = csv.writer(tx_flow_tab_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["transmission_line", "timepoint", "min_flow_mw", "max_flow_mw"]
            )

            for row in tx_flow:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)
