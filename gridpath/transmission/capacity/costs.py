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
This is a line-level module that adds to the formulation components that
describe the capacity costs of transmission lines that are available to the
optimization for each period, which depend on the line's *capacity_type*.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import join_sets
from gridpath.transmission.capacity.common_functions import (
    load_tx_capacity_type_modules,
)
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import tx_capacity_type_financial_period_sets
import gridpath.transmission.capacity.capacity_types as tx_cap_type_init


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    Before adding any components, this module will go through each relevant
    capacity type and add the module components for that capacity type.

    Then the following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_FIN_PRDS`                                                   |
    |                                                                         |
    | Two-dimensional set of the transmission lines and their financial       |
    | periods.                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`TX_LINES_FIN_IN_PRD`                                           |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set of transmission lines financial in each period.             |
    +-------------------------------------------------------------------------+
    | | :code:`FIN_PRDS_BY_TX_LINE`                                           |
    | | *Defined over*: :code:`TX_LINES`                                      |
    |                                                                         |
    | Indexed set of financial period for each transmission line.             |
    +-------------------------------------------------------------------------+
    | | :code:`TX_FIN_TMPS`                                                   |
    |                                                                         |
    | Two-dimensional set of the transmission lines and their financial       |
    | timepoints, derived from :code:`TX_FIN_PRDS` and the timepoints in each |
    | period.                                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`TX_LINES_FIN_IN_TMP`                                           |
    | | *Defined over*: :code:`TIMEPOINTS`                                    |
    |                                                                         |
    | Indexed set of transmission lines financial in each timepoint.          |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Tx_Capacity_Cost_in_Period`                                       |
    | | *Defined over*: :code:`TX_FIN_PRDS`                                   |
    |                                                                         |
    | The cost to have the transmission capacity available in the period.     |
    | Depending on the capacity type, this could be zero.                     |
    | If the subproblem is less than a full year (e.g. in production-         |
    | cost mode with 365 daily subproblems), the costs are scaled down        |
    | proportionally.                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`Total_Tx_Capacity_Costs`                                       |
    |                                                                         |
    | The total cost of the system's transmission capacity across all periods.|
    +-------------------------------------------------------------------------+

    """
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "transmission_lines.tab",
        ),
        sep="\t",
        usecols=["transmission_line", "tx_capacity_type", "tx_operational_type"],
    )

    # Required capacity modules are the unique set of tx capacity types
    # This list will be used to know which capacity modules to load
    required_tx_capacity_modules = df.tx_capacity_type.unique()

    # Import needed transmission capacity type modules for expression rules
    imported_tx_capacity_modules = load_tx_capacity_type_modules(
        required_tx_capacity_modules
    )

    # Sets
    ###########################################################################

    m.TX_FIN_PRDS = Set(
        dimen=2,
        within=m.TX_LINES * m.PERIODS,
        initialize=lambda mod: join_sets(
            mod,
            getattr(d, tx_capacity_type_financial_period_sets),
        ),
    )

    # Expressions
    ###########################################################################

    def tx_capacity_cost_rule(mod, tx, prd):
        cap_type = mod.tx_capacity_type[tx]
        if hasattr(imported_tx_capacity_modules[cap_type], "capacity_cost_rule"):
            fixed_cost = imported_tx_capacity_modules[cap_type].capacity_cost_rule(
                mod, tx, prd
            )
        else:
            fixed_cost = tx_cap_type_init.capacity_cost_rule(mod, tx, prd)

        return (
            fixed_cost
            * mod.hours_in_subproblem_period[prd]
            / mod.hours_in_period_timepoints[prd]
        )

    m.Tx_Capacity_Cost_in_Period = Expression(m.TX_FIN_PRDS, rule=tx_capacity_cost_rule)

    def tx_fixed_cost_rule(mod, tx, prd):
        """
        Get fixed cost for each lines's respective capacity module. These are
        applied in every operational period.

        Note that fixed cost inputs and calculations in the modules are on
        a period basis. Therefore, if the period spans subproblems (the main
        example of this would be specified capacity in, say, a production-cost
        scenario with multiple subproblems), we adjust the fixed costs down
        accordingly.
        """
        cap_type = mod.tx_capacity_type[tx]
        if hasattr(imported_tx_capacity_modules[cap_type], "fixed_cost_rule"):
            fixed_cost = imported_tx_capacity_modules[cap_type].fixed_cost_rule(
                mod, tx, prd
            )
        else:
            fixed_cost = tx_cap_type_init.fixed_cost_rule(mod, tx, prd)

        return (
            fixed_cost
            * mod.hours_in_subproblem_period[prd]
            / mod.hours_in_period_timepoints[prd]
        )

    m.Tx_Fixed_Cost_in_Period = Expression(m.TX_OPR_PRDS, rule=tx_fixed_cost_rule)


# Input-Output
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
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "transmission_lines.tab",
        ),
        sep="\t",
        usecols=["transmission_line", "tx_capacity_type", "tx_operational_type"],
    )

    # Required capacity modules are the unique set of tx capacity types
    # This list will be used to know which capacity modules to load
    required_tx_capacity_modules = df.tx_capacity_type.unique()

    # Import needed transmission capacity type modules for expression rules
    imported_tx_capacity_modules = load_tx_capacity_type_modules(
        required_tx_capacity_modules
    )

    # Add model components for each of the transmission capacity modules
    for op_m in required_tx_capacity_modules:
        if hasattr(imported_tx_capacity_modules[op_m], "load_model_data"):
            imported_tx_capacity_modules[op_m].load_model_data(
                m, d, data_portal, scenario_directory, subproblem, stage
            )
        else:
            pass


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "transmission_lines.tab",
        ),
        sep="\t",
        usecols=["transmission_line", "tx_capacity_type", "tx_operational_type"],
    )

    # Required capacity modules are the unique set of tx capacity types
    # This list will be used to know which capacity modules to load
    # Module-specific results
    required_tx_capacity_modules = df.tx_capacity_type.unique()

    # Import needed transmission capacity type modules for expression rules
    imported_tx_capacity_modules = load_tx_capacity_type_modules(
        required_tx_capacity_modules
    )

    # Add model components for each of the transmission capacity modules
    for op_m in required_tx_capacity_modules:
        if hasattr(imported_tx_capacity_modules[op_m], "export_results"):
            imported_tx_capacity_modules[op_m].export_results(
                m, d, scenario_directory, subproblem, stage
            )
        else:
            pass

    # Export transmission capacity costs
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "costs_transmission_capacity.csv",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "tx_line",
                "period",
                "hours_in_period_timepoints",
                "hours_in_subproblem_period",
                "load_zone_from",
                "load_zone_to",
                "capacity_cost",
                "fixed_cost",
            ]
        )

        for l, p in m.TX_FIN_PRDS:
            writer.writerow(
                [
                    l,
                    p,
                    m.hours_in_period_timepoints[p],
                    m.hours_in_subproblem_period[p],
                    m.load_zone_from[l],
                    m.load_zone_to[l],
                    value(m.Tx_Capacity_Cost_in_Period[l, p]),
                ]
            )

    # TODO: add fixed costs when consolidating line-period results


def save_duals(scenario_directory, subproblem, stage, instance, dynamic_components):
    # Save module-specific duals
    # Capacity type modules
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "transmission_lines.tab",
        ),
        sep="\t",
        usecols=["transmission_line", "tx_capacity_type", "tx_operational_type"],
    )

    # Required capacity modules are the unique set of tx capacity types
    # This list will be used to know which capacity modules to load
    required_tx_capacity_modules = df.tx_capacity_type.unique()

    # Import needed transmission capacity type modules for expression rules
    imported_tx_capacity_modules = load_tx_capacity_type_modules(
        required_tx_capacity_modules
    )

    # Add any components specific to the operational modules
    for op_m in required_tx_capacity_modules:
        if hasattr(imported_tx_capacity_modules[op_m], "save_duals"):
            imported_tx_capacity_modules[op_m].save_duals(
                scenario_directory,
                subproblem,
                stage,
                instance,
                dynamic_components,
            )
        else:
            pass


# Database
###############################################################################


def import_results_into_database(
    scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    # Tx capacity results
    if not quiet:
        print("transmission capacity")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_transmission_capacity",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "transmission_capacity.csv"), "r"
    ) as capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        next(reader)  # skip header
        for row in reader:
            tx_line = row[0]
            period = row[1]
            load_zone_from = row[2]
            load_zone_to = row[3]
            min_mw = row[4]
            max_mw = row[5]

            results.append(
                (
                    scenario_id,
                    tx_line,
                    period,
                    subproblem,
                    stage,
                    load_zone_from,
                    load_zone_to,
                    min_mw,
                    max_mw,
                )
            )

    insert_temp_sql = """
        INSERT INTO temp_results_transmission_capacity{}
            (scenario_id, tx_line, period, subproblem_id, stage_id,
            load_zone_from, load_zone_to,
            min_mw, max_mw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_capacity
        (scenario_id, tx_line, period, subproblem_id, stage_id,
        load_zone_from, load_zone_to, min_mw, max_mw)
        SELECT
        scenario_id, tx_line, period, subproblem_id, stage_id,
        load_zone_from, load_zone_to, min_mw, max_mw
        FROM temp_results_transmission_capacity{}
         ORDER BY scenario_id, tx_line, period, subproblem_id, stage_id;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)

    # Capacity cost results
    if not quiet:
        print("transmission capacity costs")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_transmission_costs_capacity",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "costs_transmission_capacity.csv"), "r"
    ) as capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        next(reader)  # skip header
        for row in reader:
            tx_line = row[0]
            period = row[1]
            hours_in_period_timepoints = row[2]
            hours_in_subproblem_period = row[3]
            load_zone_from = row[4]
            load_zone_to = row[5]
            capacity_cost = row[6]

            results.append(
                (
                    scenario_id,
                    tx_line,
                    period,
                    subproblem,
                    stage,
                    hours_in_period_timepoints,
                    hours_in_subproblem_period,
                    load_zone_from,
                    load_zone_to,
                    capacity_cost,
                )
            )

    insert_temp_sql = """
        INSERT INTO  temp_results_transmission_costs_capacity{}
        (scenario_id, tx_line, period, subproblem_id, stage_id,
        hours_in_period_timepoints, hours_in_subproblem_period,
        load_zone_from, load_zone_to, capacity_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_costs_capacity
        (scenario_id, tx_line, period, subproblem_id, stage_id, 
        hours_in_period_timepoints, hours_in_subproblem_period,
        load_zone_from, load_zone_to, capacity_cost)
        SELECT
        scenario_id, tx_line, period, subproblem_id, stage_id,
        hours_in_period_timepoints, hours_in_subproblem_period, 
        load_zone_from, load_zone_to, capacity_cost
        FROM temp_results_transmission_costs_capacity{}
         ORDER BY scenario_id, tx_line, period, subproblem_id, stage_id;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)

    # Update the capacity cost removing the fraction attributable to the
    # spinup and lookahead hours
    update_sql = """
        UPDATE results_transmission_costs_capacity
        SET capacity_cost_wo_spinup_or_lookahead = capacity_cost * (
            SELECT fraction_of_hours_in_subproblem
            FROM spinup_or_lookahead_ratios
            WHERE spinup_or_lookahead = 0
            AND results_transmission_costs_capacity.scenario_id = 
            spinup_or_lookahead_ratios.scenario_id
            AND results_transmission_costs_capacity.subproblem_id = 
            spinup_or_lookahead_ratios.subproblem_id
            AND results_transmission_costs_capacity.stage_id = 
            spinup_or_lookahead_ratios.stage_id
            AND results_transmission_costs_capacity.period = 
            spinup_or_lookahead_ratios.period
        )
        ;
    """

    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=(), many=False)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """
    Aggregate capacity costs by "to_zone" load zone, and break out into
    spinup_or_lookahead.
    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("aggregate tx capacity costs by load zone")

    # Delete old resulst
    del_sql = """
        DELETE FROM results_transmission_costs_capacity_agg 
        WHERE scenario_id = ?
        """
    spin_on_database_lock(
        conn=db, cursor=c, sql=del_sql, data=(scenario_id,), many=False
    )

    # Insert new results
    agg_sql = """
        INSERT INTO results_transmission_costs_capacity_agg
        (scenario_id, load_zone, period, subproblem_id, stage_id,
        spinup_or_lookahead, fraction_of_hours_in_subproblem, capacity_cost)

        SELECT scenario_id, load_zone, period, subproblem_id, stage_id,
        spinup_or_lookahead, fraction_of_hours_in_subproblem,
        (capacity_cost * fraction_of_hours_in_subproblem) AS capacity_cost
        FROM spinup_or_lookahead_ratios

        -- Add load_zones
        LEFT JOIN
        (SELECT scenario_id, load_zone
        FROM inputs_geography_load_zones
        INNER JOIN
        (SELECT scenario_id, load_zone_scenario_id FROM scenarios
        WHERE scenario_id = ?) AS scen_tbl
        USING (load_zone_scenario_id)
        ) AS lz_tbl
        USING (scenario_id)

        -- Now that we have all scenario_id, subproblem_id, stage_id, period, 
        -- load_zone, and spinup_or_lookahead combinations add the tx capacity 
        -- costs which will be derated by the fraction_of_hours_in_subproblem
        INNER JOIN
        (SELECT scenario_id, subproblem_id, stage_id, period, 
        load_zone_to AS load_zone,
        SUM(capacity_cost) AS capacity_cost
        FROM results_transmission_costs_capacity
        GROUP BY scenario_id, subproblem_id, stage_id, period, load_zone
        ) AS cap_table
        USING (scenario_id, subproblem_id, stage_id, period, load_zone)
        ;"""

    spin_on_database_lock(
        conn=db, cursor=c, sql=agg_sql, data=(scenario_id,), many=False
    )
