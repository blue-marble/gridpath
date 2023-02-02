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
describe the amount of power flowing on each line.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.transmission.operations.common_functions import (
    load_tx_operational_type_modules,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Transmit_Power_MW`                                        |
    | | *Defined over*: :code:`TX_OPR_TMPS`                                   |
    |                                                                         |
    | The power in MW sent on a transmission line (before losses).            |
    | A positive number means the power flows in the line's defined direction,|
    | while a negative number means it flows in the opposite direction.       |
    +-------------------------------------------------------------------------+
    | | :code:`Transmit_Power_MW`                                    |
    | | *Defined over*: :code:`TX_OPR_TMPS`                                   |
    |                                                                         |
    | The power in MW received via a transmission line (after losses).        |
    | A positive number means the power flows in the line's defined direction,|
    | while a negative number means it flows in the opposite direction.       |
    +-------------------------------------------------------------------------+
    | | :code:`Tx_Losses_MW`                                                  |
    | | *Defined over*: :code:`TX_OPR_TMPS`                                   |
    |                                                                         |
    | Losses on the transmission line in MW. A positive number means the      |
    | power flows in the line's defined direction when losses incurred,       |
    | while a negative number means it flows in the opposite direction.       |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Inputs
    ###########################################################################

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

    required_tx_operational_modules = df.tx_operational_type.unique()

    # Import needed transmission operational type modules
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_operational_modules
    )

    # TODO: should we add the module specific components here or in
    #  operational_types/__init__.py? Doing it in __init__.py to be consistent
    #  with projects/operations/power.py

    # Expressions
    ###########################################################################

    def transmit_power_rule(mod, tx, tmp):
        tx_op_type = mod.tx_operational_type[tx]
        return imported_tx_operational_modules[tx_op_type].transmit_power_rule(
            mod, tx, tmp
        )

    m.Transmit_Power_MW = Expression(m.TX_OPR_TMPS, rule=transmit_power_rule)

    def transmit_power_losses_lz_from_rule(mod, tx, tmp):
        tx_op_type = mod.tx_operational_type[tx]
        return imported_tx_operational_modules[
            tx_op_type
        ].transmit_power_losses_lz_from_rule(mod, tx, tmp)

    m.Tx_Losses_LZ_From_MW = Expression(
        m.TX_OPR_TMPS, rule=transmit_power_losses_lz_from_rule
    )

    def transmit_power_losses_lz_to_rule(mod, tx, tmp):
        tx_op_type = mod.tx_operational_type[tx]
        return imported_tx_operational_modules[
            tx_op_type
        ].transmit_power_losses_lz_to_rule(mod, tx, tmp)

    m.Tx_Losses_LZ_To_MW = Expression(
        m.TX_OPR_TMPS, rule=transmit_power_losses_lz_to_rule
    )


# Input-Output
###############################################################################


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m: The Pyomo abstract model
    :param d: Dynamic components
    :return: Nothing
    """

    # Transmission flows for all lines
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "transmission_operations.csv",
        ),
        "w",
        newline="",
    ) as tx_op_results_file:
        writer = csv.writer(tx_op_results_file)
        writer.writerow(
            [
                "tx_line",
                "lz_from",
                "lz_to",
                "timepoint",
                "period",
                "timepoint_weight",
                "number_of_hours_in_timepoint",
                "transmission_flow_mw",
                "transmission_losses_lz_from",
                "transmission_losses_lz_to",
            ]
        )
        for l, tmp in m.TX_OPR_TMPS:
            writer.writerow(
                [
                    l,
                    m.load_zone_from[l],
                    m.load_zone_to[l],
                    tmp,
                    m.period[tmp],
                    m.tmp_weight[tmp],
                    m.hrs_in_tmp[tmp],
                    value(m.Transmit_Power_MW[l, tmp]),
                    value(m.Tx_Losses_LZ_From_MW[l, tmp]),
                    value(m.Tx_Losses_LZ_To_MW[l, tmp]),
                ]
            )

    # TODO: does this belong here or in operational_types/__init__.py?
    #  (putting it here to be in line with projects/operations/power.py)
    # Module-specific transmission operational results
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

    required_tx_operational_modules = df.tx_operational_type.unique()

    # Import needed transmission operational type modules
    imported_tx_operational_modules = load_tx_operational_type_modules(
        required_tx_operational_modules
    )
    for op_m in required_tx_operational_modules:
        if hasattr(imported_tx_operational_modules[op_m], "export_results"):
            imported_tx_operational_modules[op_m].export_results(
                m,
                d,
                scenario_directory,
                subproblem,
                stage,
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
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    if not quiet:
        print("transmission operations")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_transmission_operations",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "transmission_operations.csv"), "r"
    ) as tx_op_file:
        reader = csv.reader(tx_op_file)

        next(reader)  # skip header
        for row in reader:
            tx_line = row[0]
            lz_from = row[1]
            lz_to = row[2]
            timepoint = row[3]
            period = row[4]
            timepoint_weight = row[5]
            number_of_hours_in_timepoint = row[6]
            tx_sent = row[7]
            tx_losses_lz_from = row[8]
            tx_losses_lz_to = row[9]

            results.append(
                (
                    scenario_id,
                    tx_line,
                    period,
                    subproblem,
                    stage,
                    timepoint,
                    timepoint_weight,
                    number_of_hours_in_timepoint,
                    lz_from,
                    lz_to,
                    tx_sent,
                    tx_losses_lz_from,
                    tx_losses_lz_to,
                )
            )

    insert_temp_sql = """
        INSERT INTO temp_results_transmission_operations{}
        (scenario_id, transmission_line, period, subproblem_id, 
        stage_id, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, transmission_flow_mw,
        transmission_losses_lz_from, transmission_losses_lz_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_operations
        (scenario_id, transmission_line, period, subproblem_id, stage_id,
        timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, transmission_flow_mw,
        transmission_losses_lz_from, transmission_losses_lz_to)
        SELECT
        scenario_id, transmission_line, period, subproblem_id, stage_id,
        timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, transmission_flow_mw,
        transmission_losses_lz_from, transmission_losses_lz_to
        FROM temp_results_transmission_operations{}
         ORDER BY scenario_id, transmission_line, subproblem_id, stage_id, 
        timepoint;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """
    Aggregate imports/exports by zone, period and spinup_or_lookahead
    (numbers are based on flows without accounting for losses!)
    TODO: add losses?
    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("aggregate transmission imports exports")

    # Delete old results
    del_sql = """
        DELETE FROM results_transmission_imports_exports_agg
        WHERE scenario_id = ?
        """
    spin_on_database_lock(
        conn=db, cursor=c, sql=del_sql, data=(scenario_id,), many=False
    )

    # Aggregate imports/exports by period, load zone, and spinup_or_lookahead
    agg_sql = """
        INSERT INTO results_transmission_imports_exports_agg
        (scenario_id, subproblem_id, stage_id, period, 
        load_zone, spinup_or_lookahead, imports, exports)
        
        SELECT scenario_id, subproblem_id, stage_id, period, load_zone,
        spinup_or_lookahead,
        (IFNULL(imports_pos_dir,0) + IFNULL(imports_neg_dir,0)) AS imports,
        (IFNULL(exports_pos_dir,0) + IFNULL(exports_neg_dir,0)) AS exports
        
        FROM (
        
        -- dummy required to make sure all load zones are included 
        -- (SQLite cannot do full outer join)
        
        SELECT DISTINCT scenario_id, subproblem_id, stage_id, period, load_zone,
        spinup_or_lookahead
        FROM (
            SELECT scenario_id, subproblem_id, stage_id, period, load_zone, 
            spinup_or_lookahead
            FROM (
                (SELECT DISTINCT scenario_id, subproblem_id, stage_id, period, 
                load_zone_to AS load_zone, spinup_or_lookahead
                FROM results_transmission_operations
                WHERE scenario_id = ?) AS dummy
                
                LEFT JOIN 
                
                (SELECT DISTINCT scenario_id, subproblem_id, stage_id, period, 
                load_zone_from AS load_zone, spinup_or_lookahead
                FROM results_transmission_operations
                WHERE scenario_id = ?) AS dummy2
                USING (scenario_id, subproblem_id, stage_id, period, load_zone,
                spinup_or_lookahead)
            ) AS left_join1
            
            UNION ALL
        
            SELECT scenario_id, subproblem_id, stage_id, period, load_zone,
            spinup_or_lookahead
            FROM (
                (SELECT DISTINCT scenario_id, subproblem_id, stage_id, period, 
                load_zone_from AS load_zone, spinup_or_lookahead
                FROM results_transmission_operations
                WHERE scenario_id = ?) AS dummy3
                
                LEFT JOIN 
                
                (SELECT DISTINCT scenario_id, subproblem_id, stage_id, period, 
                load_zone_to AS load_zone, spinup_or_lookahead
                FROM results_transmission_operations
                WHERE scenario_id = ?) AS dummy4
                USING (scenario_id, subproblem_id, stage_id, period, load_zone,
                spinup_or_lookahead)
            
            ) AS left_join2
        
        ) AS outer_join_table
        
        ) AS distinct_outer_join_table
                        
        LEFT JOIN
        
        (SELECT scenario_id, subproblem_id, stage_id, period, 
        load_zone_to AS load_zone, spinup_or_lookahead,
        SUM(transmission_flow_mw * timepoint_weight * 
        number_of_hours_in_timepoint) AS imports_pos_dir
        FROM results_transmission_operations
        WHERE transmission_flow_mw > 0
        AND scenario_id = ?
        GROUP BY scenario_id, subproblem_id, stage_id, period, load_zone, 
        spinup_or_lookahead) 
        AS imports_pos_dir
        USING (scenario_id, subproblem_id, stage_id, period, load_zone,
        spinup_or_lookahead)
        
        LEFT JOIN
        
        (SELECT scenario_id, subproblem_id, stage_id, period, 
        load_zone_from AS load_zone, spinup_or_lookahead,
        SUM(transmission_flow_mw * timepoint_weight * 
        number_of_hours_in_timepoint) AS exports_pos_dir
        FROM results_transmission_operations
        WHERE transmission_flow_mw > 0
        AND scenario_id = ?
        GROUP BY scenario_id, subproblem_id, stage_id, period, load_zone, 
        spinup_or_lookahead) 
        AS exports_pos_dir
        USING (scenario_id, subproblem_id, stage_id, period, load_zone,
        spinup_or_lookahead)
        
        LEFT JOIN
        
        (SELECT scenario_id, subproblem_id, stage_id, period, 
        load_zone_from AS load_zone, spinup_or_lookahead,
        -SUM(transmission_flow_mw * timepoint_weight * 
        number_of_hours_in_timepoint) AS imports_neg_dir
        FROM results_transmission_operations
        WHERE transmission_flow_mw < 0
        AND scenario_id = ?
        GROUP BY scenario_id, subproblem_id, stage_id, period, load_zone,
        spinup_or_lookahead) 
        AS imports_neg_dir
        USING (scenario_id, subproblem_id, stage_id,period, load_zone,
        spinup_or_lookahead)
        
        LEFT JOIN
        
        (SELECT scenario_id, subproblem_id, stage_id, period, 
        load_zone_to AS load_zone, spinup_or_lookahead,
        -SUM(transmission_flow_mw * timepoint_weight * 
        number_of_hours_in_timepoint) AS exports_neg_dir
        FROM results_transmission_operations
        WHERE transmission_flow_mw < 0
        AND scenario_id = ?
        GROUP BY scenario_id, subproblem_id, stage_id, period, load_zone,
        spinup_or_lookahead) 
        AS exports_neg_dir
        USING (scenario_id, subproblem_id, stage_id, period, load_zone,
        spinup_or_lookahead)
        
        ORDER BY subproblem_id, stage_id, period, load_zone, spinup_or_lookahead
        ;"""

    scenario_ids = tuple([scenario_id] * 8)
    spin_on_database_lock(conn=db, cursor=c, sql=agg_sql, data=scenario_ids, many=False)
