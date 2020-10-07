#!/usr/bin/env python
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
This module enforces limits on flows across groups of transmission lines.
Right now, "flows" are defined as power sent on these lines. It is not
recommended that this module be used if you are modeling line losses.

TODO: what is the meaning of simultaneous flow limit if we have losses on
    the lines, i.e. should we use power sent or power received? We should
    probably have an extra input that defines whether to use power sent or
    power received in determining flow on the line.
"""


import csv
import os.path
from pyomo.environ import Set, Param, Constraint, NonNegativeReals, \
    Integers, Expression, value


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`SIM_FLOW_LMTS`                                                 |
    |                                                                         |
    | The set of simultaneous flow limits being modeled.                      |
    +-------------------------------------------------------------------------+
    | | :code:`SIM_FLOW_LMT_PRDS`                                             |
    |                                                                         |
    | Two-dimensional set of the simultaneous flow limits and the periods     |
    | periods in which they are active.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`SIM_FLOW_LMT_TMPS`                                             |
    |                                                                         |
    | Two-dimensional set of the simultaneous flow limits in each             |
    | operational timepoint.                                                  |
    +-------------------------------------------------------------------------+
    | | :code:`SIM_FLOW_LMT_TX_LINES`                                         |
    |                                                                         |
    | Two-dimensional set of the simultaneous flow limits and its associated  |
    | transmission lines.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`TX_LINES_BY_SIM_FLOW_LMT`                                      |
    | | *Defined over*: :code:`SIM_FLOW_LMTS`                                 |
    |                                                                         |
    | Indexed set describing the transmission lines associated with each      |
    | simultaneous flow limit group.                                          |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`sim_flow_lmt_mw`                                               |
    | | *Defined over*: :code:`SIM_FLOW_LMT_PRDS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The flow limit in MW for each simultaneous flow limit group in each     |
    | operational period, e.g. the sum of all imports into the CAISO zone     |
    | cannot exceed 10,000 MW.                                                |
    +-------------------------------------------------------------------------+
    | | :code:`sim_flow_direction`                                            |
    | | *Defined over*: :code:`SIM_FLOW_LMT_TX_LINES`                         |
    | | *Within*: :code:`Integers [-1, 1]`                                    |
    |                                                                         |
    | For each transmission line in each simultaneous flow limit group, this  |
    | param describes in which direction the transmission line is added into  |
    | the flow limit constraint.                                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Sim_Flow_MW`                                                   |
    | | *Defined over*: :code:`SIM_FLOW_LMT_TMPS`                             |
    |                                                                         |
    | The total flow on lines in each simultaneous flow limit group,          |
    | according to their specified direction in :code:`sim_flow_direction`    |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`Sim_Flow_Constrain                                             |
    | | *Enforced over*: :code:`SIM_FLOW_LMT_TMPS`                            |
    |                                                                         |
    | The total flow on lines in each simultaneous flow limit group shall     |
    | not exceed the simultaneous flow limit group's limit.                   |
    +-------------------------------------------------------------------------+

    """

    m.SIM_FLOW_LMT_PRDS = Set(dimen=2)

    m.SIM_FLOW_LMT_TMPS = Set(
        dimen=2,
        initialize=lambda mod: list(
            set((g, tmp) for (g, p) in mod.SIM_FLOW_LMT_PRDS
                for tmp in mod.TMPS_IN_PRD[p])
        )
    )

    m.SIM_FLOW_LMTS = Set(
        initialize=lambda mod: list(
            set(limit for (limit, period) in mod.SIM_FLOW_LMT_PRDS)
        )
    )

    m.SIM_FLOW_LMT_TX_LINES = Set(
        dimen=2,
        within=m.SIM_FLOW_LMTS * m.TX_LINES
    )

    m.TX_LINES_BY_SIM_FLOW_LMT = Set(
        m.SIM_FLOW_LMTS,
        initialize=lambda mod, limit: list(
            set(tx_line for (group, tx_line)
                in mod.SIM_FLOW_LMT_TX_LINES if group == limit)
        )
    )

    # Required Input Params
    ###########################################################################

    m.sim_flow_lmt_mw = Param(
        m.SIM_FLOW_LMT_PRDS,
        within=NonNegativeReals
    )

    m.sim_flow_direction = Param(
        m.SIM_FLOW_LMT_TX_LINES,
        within=Integers,
        validate=lambda mod, v, g, l: v in [-1, 1]
    )

    # Expressions
    ###########################################################################

    m.Sim_Flow_MW = Expression(
        m.SIM_FLOW_LMT_TMPS,
        rule=sim_flow_expression_rule
    )

    # Constraints
    ###########################################################################

    m.Sim_Flow_Constraint = Constraint(
        m.SIM_FLOW_LMT_TMPS,
        rule=sim_flow_constraint_rule
    )


# Expression Rules
###############################################################################

def sim_flow_expression_rule(mod, g, tmp):
    """
    **Expression Name**: Sim_Flow_MW
    **Defined Over**: SIM_FLOW_LMT_TMPS

    Total flow on lines in each simultaneous flow group.
    """
    return sum(mod.Transmit_Power_MW[tx_line, tmp]
               * mod.sim_flow_direction[g, tx_line]
               for tx_line in mod.TX_LINES_BY_SIM_FLOW_LMT[g]
               if (tx_line, tmp) in mod.TX_OPR_TMPS)


# Constraint Formulation Rules
###############################################################################

def sim_flow_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: Sim_Flow_Constraint
    **Enforced Over**: SIM_FLOW_LMT_TMPS

    Total flow on lines in each simultaneous flow group cannot exceed limit.
    """
    return mod.Sim_Flow_MW[g, tmp] \
        <= mod.sim_flow_lmt_mw[g, mod.period[tmp]]


# Input-Outputs
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                              "transmission_simultaneous_flow_limits.tab"),
        select=("simultaneous_flow_limit", "period",
                "simultaneous_flow_limit_mw"),
        index=m.SIM_FLOW_LMT_PRDS,
        param=m.sim_flow_lmt_mw
    )

    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                              "transmission_simultaneous_flow_limit_lines.tab"),
        select=("simultaneous_flow_limit", "transmission_line",
                "simultaneous_flow_direction"),
        index=m.SIM_FLOW_LMT_TX_LINES,
        param=m.sim_flow_direction
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export transmission operations
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "transmission_simultaneous_flow_limits.csv"),
              "w", newline="") as tx_op_results_file:
        writer = csv.writer(tx_op_results_file)
        writer.writerow(["simultaneous_flow_limit", "timepoint", "period",
                         "timepoint_weight", "simultaneous_flow_mw"])
        for (g, tmp) in m.SIM_FLOW_LMT_TMPS:
            writer.writerow([
                g,
                tmp,
                m.period[tmp],
                m.tmp_weight[tmp],
                value(m.Sim_Flow_MW[g, tmp])
            ])


def save_duals(m):
    m.constraint_indices["Sim_Flow_Constraint"] = \
        ["sim_flow_lmt", "timepoint", "dual"]


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
    c1 = conn.cursor()
    flow_limits = c1.execute(
        """SELECT transmission_simultaneous_flow_limit, period, max_flow_mw
        FROM inputs_transmission_simultaneous_flow_limits
        INNER JOIN
        (SELECT period
         FROM inputs_temporal_periods
         WHERE temporal_scenario_id = {}) as relevant_periods
         USING (period)
         WHERE transmission_simultaneous_flow_limit_scenario_id = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID
        )
    )

    c2 = conn.cursor()
    limit_lines = c2.execute(
        """SELECT transmission_simultaneous_flow_limit, transmission_line,
        simultaneous_flow_direction
        FROM inputs_transmission_simultaneous_flow_limit_line_groups
        INNER JOIN
        (SELECT DISTINCT transmission_simultaneous_flow_limit
        FROM inputs_transmission_simultaneous_flow_limits
        WHERE transmission_simultaneous_flow_limit_scenario_id = {}) as
        relevant_limits
        USING (transmission_simultaneous_flow_limit)
        INNER JOIN
        (SELECT transmission_line
        FROM inputs_transmission_portfolios
        WHERE transmission_portfolio_scenario_id = {})
        USING (transmission_line)
        WHERE transmission_simultaneous_flow_limit_line_group_scenario_id
        = {};
        """.format(
            subscenarios.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID,
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID,
            subscenarios.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_LINE_SCENARIO_ID
        )
    )

    return flow_limits, limit_lines


def write_model_inputs(
        scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    transmission_simultaneous_flow_limits.tab and
    transmission_simultaneous_flow_limit_lines files.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    flow_limits, limit_lines = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    # transmission_simultaneous_flow_limits.tab
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "transmission_simultaneous_flow_limits.tab"),
              "w", newline="") as sim_flows_file:
        writer = csv.writer(sim_flows_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["simultaneous_flow_limit", "period", "simultaneous_flow_limit_mw"]
        )

        for row in flow_limits:
            writer.writerow(row)

    # transmission_simultaneous_flow_limit_lines.tab
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "transmission_simultaneous_flow_limit_lines.tab"),
              "w", newline="") as sim_flow_limit_lines_file:
        writer = csv.writer(sim_flow_limit_lines_file,
                            delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["simultaneous_flow_limit", "transmission_line",
             "simultaneous_flow_direction"]
        )

        for row in limit_lines:
            writer.writerow(row)


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
    pass
    # Validation to be added
    # flow_limits, limit_lines = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)

