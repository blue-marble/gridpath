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
This capacity type describes transmission lines that are available to the
optimization without having to incur an investment cost, e.g. existing
lines or lines that will be built in the future and whose capital costs
we want to ignore (in the objective function). A specified transmission line
can be available in all periods, or in some periods only, with no
restriction on the order and combination of periods. The two transmission
line directions may have different specified capacities, e.g. a line from
Zone 1 to Zone 2 with a minimum flow capacity of -1,000 MW and a maximum flow
capacity of 1,200 MW can transmit up to 1,000 MW from Zone 2 to Zone 1 and
up to 1,200 MW from Zone 1 to Zone 2.

"""

import csv
import os.path
from pyomo.environ import Set, Param, Reals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.dynamic_components import \
    tx_capacity_type_operational_period_sets
from gridpath.auxiliary.validations import get_tx_lines, get_expected_dtypes, \
    write_validation_to_database, validate_dtypes, \
    validate_idxs, validate_missing_inputs, validate_column_monotonicity


# TODO: add fixed O&M costs similar to gen_spec
def add_model_components(
        m, d, scenario_directory, subproblem, stage
):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_SPEC_OPR_PRDS`                                              |
    |                                                                         |
    | Two-dimensional set of transmission line-period combinations that       |
    | helps describe the transmission capacity available in a given period.   |
    | This set is added to the list of sets to join to get the final          |
    | :code:`TX_OPR_PRDS` set defined in                                      |
    | **gridpath.transmission.capacity.capacity**.                            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`tx_spec_min_flow_mw`                                           |
    | | *Defined over*: :code:`TX_SPEC_OPR_PRDS`                              |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | The transmission line's specified minimum flow capacity (in MW) in      |
    | each operational period. A negative number designates flow in the       |
    | opposite direction of the defined line flow direction.                  |
    +-------------------------------------------------------------------------+
    | | :code:`tx_spec_max_flow_mw`                                           |
    | | *Defined over*: :code:`TX_SPEC_OPR_PRDS`                              |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | The transmission line's specified maximum flow capacity (in MW) in      |
    | each operational period. A negative number designates flow in the       |
    | opposite direction of the defined line flow direction.                  |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.TX_SPEC_OPR_PRDS = Set(dimen=2)

    # Required Params
    ###########################################################################

    m.tx_spec_min_flow_mw = Param(
        m.TX_SPEC_OPR_PRDS,
        within=Reals
    )
    m.tx_spec_max_flow_mw = Param(
        m.TX_SPEC_OPR_PRDS,
        within=Reals
    )

    # Dynamic Components
    ###########################################################################

    getattr(d, tx_capacity_type_operational_period_sets).append(
        "TX_SPEC_OPR_PRDS"
    )


# Transmission Capacity Type Methods
###############################################################################

def min_transmission_capacity_rule(mod, tx, p):
    return mod.tx_spec_min_flow_mw[tx, p]


def max_transmission_capacity_rule(mod, tx, p):
    return mod.tx_spec_max_flow_mw[tx, p]


def tx_capacity_cost_rule(mod, g, p):
    """
    None for now.
    TODO: should there be a fixed cost for keeping transmission around
    """
    return 0


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory,
                              subproblem, stage):
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                              "specified_transmission_line_capacities.tab"),
        select=("transmission_line", "period",
                "specified_tx_min_mw", "specified_tx_max_mw"),
        index=m.TX_SPEC_OPR_PRDS,
        param=(m.tx_spec_min_flow_mw,
               m.tx_spec_max_flow_mw)
    )


# Database
###############################################################################

def get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    tx_capacities = c.execute(
        """SELECT transmission_line, period, min_mw, max_mw
        FROM inputs_transmission_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT transmission_line, period, min_mw, max_mw
        FROM inputs_transmission_specified_capacity
        WHERE transmission_specified_capacity_scenario_id = {} ) as capacity
        USING (transmission_line, period)
        WHERE transmission_portfolio_scenario_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
        )
    )

    return tx_capacities


def write_model_model_inputs(
        scenario_directory, scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    specified_transmission_line_capacities.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tx_capacities = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "specified_transmission_line_capacities.tab"),
              "w", newline="") as existing_tx_capacity_tab_file:
        writer = csv.writer(existing_tx_capacity_tab_file,
                            delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["transmission_line", "period", "specified_tx_min_mw",
             "specified_tx_max_mw"]
        )

        for row in tx_capacities:
            writer.writerow(row)


# Validation
###############################################################################

def validate_model_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tx_capacities = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    tx_lines = get_tx_lines(conn, scenario_id, subscenarios, "capacity_type", "tx_spec")

    # Convert input data into pandas DataFrame and extract data
    df = cursor_to_df(tx_capacities)
    spec_tx_lines = df["transmission_line"].unique()

    # Get expected dtypes
    expected_dtypes = get_expected_dtypes(
        conn=conn,
        tables=["inputs_transmission_specified_capacity"]
    )

    # Check dtypes
    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_specified_capacity",
        severity="High",
        errors=dtype_errors
    )

    # Ensure tx_line capacity is specified in at least 1 period
    msg = "Expected specified capacity for at least one period."
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_specified_capacity",
        severity="High",
        errors=validate_idxs(actual_idxs=spec_tx_lines,
                             req_idxs=tx_lines,
                             idx_label="transmission_line",
                             msg=msg)
    )

    # Check for missing values (vs. missing row entries above)
    cols = ["min_mw", "max_mw"]
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_specified_capacity",
        severity="High",
        errors=validate_missing_inputs(df, cols)
    )

    # check that min <= max
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_potential",
        severity="High",
        errors=validate_column_monotonicity(
            df=df,
            cols=cols,
            idx_col=["project", "period"]
        )
    )
