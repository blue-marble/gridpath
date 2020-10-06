#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a line-level module that adds to the formulation components that
describe the capacity of transmission lines that are available to the
optimization for each period. The capacity can be a fixed  number or an
expression with variables depending on the line's *capacity_type*. The
project capacity can then be used to constrain operations, contribute to
reliability constraints, etc. The module also adds transmission costs which
again depend on the line's *capacity_type*.
"""

import csv
from functools import reduce
import os.path
import pandas as pd
from pyomo.environ import Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import join_sets
from gridpath.transmission.capacity.common_functions import \
    load_tx_capacity_type_modules
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import \
    tx_capacity_type_operational_period_sets


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    Before adding any components, this module will go through each relevant
    capacity type and add the module components for that capacity type.

    Then the following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_OPR_PRDS`                                                   |
    |                                                                         |
    | Two-dimensional set of the transmission lines and their operational     |
    | periods (capacity exists and is available).                             |
    +-------------------------------------------------------------------------+
    | | :code:`TX_LINES_OPR_IN_PRD`                                           |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set of transmission lines operational in each period.           |
    +-------------------------------------------------------------------------+
    | | :code:`OPR_PRDS_BY_TX_LINE`                                           |
    | | *Defined over*: :code:`TX_LINES`                                      |
    |                                                                         |
    | Indexed set of operational period for each transmission line.           |
    +-------------------------------------------------------------------------+
    | | :code:`TX_OPR_TMPS`                                                   |
    |                                                                         |
    | Two-dimensional set of the transmission lines and their operational     |
    | timepoints, derived from :code:`TX_OPR_PRDS` and the timepoitns in each |
    | period.                                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`TX_LINES_OPR_IN_TMP`                                           |
    | | *Defined over*: :code:`TIMEPOINTS`                                    |
    |                                                                         |
    | Indexed set of transmission lines operatoinal in each timepoint.        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Tx_Min_Capacity_MW`                                            |
    | | *Defined over*: :code:`TX_OPR_PRDS`                                   |
    |                                                                         |
    | The transmission line's minimum flow in MW (negative number indicates   |
    | flow in the opposite direction of the line's defined flow direction).   |
    | Depending on the capacity type, this can be a pre-specified amount or   |
    | a decision variable (with an associated cost).                          |
    +-------------------------------------------------------------------------+
    | | :code:`Tx_Max_Capacity_MW`                                            |
    | | *Defined over*: :code:`TX_OPR_PRDS`                                   |
    |                                                                         |
    | The transmission line's maximum flow in MW (negative number indicates   |
    | flow in the opposite direction of the line's defined flow direction).   |
    | Depending on the capacity type, this can be a pre-specified amount or   |
    | a decision variable (with an associated cost).                          |
    +-------------------------------------------------------------------------+
    | | :code:`Tx_Capacity_Cost_in_Prd`                                       |
    | | *Defined over*: :code:`TX_OPR_PRDS`                                   |
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

    # Dynamic Inputs
    ###########################################################################

    df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                     "transmission_lines.tab"),
        sep="\t",
        usecols=["TRANSMISSION_LINES", "tx_capacity_type",
                 "tx_operational_type"]
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
        imp_op_m = imported_tx_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_model_components"):
            imp_op_m.add_model_components(
                m, d, scenario_directory, subproblem, stage
            )

    # Sets
    ###########################################################################

    m.TX_OPR_PRDS = Set(
        dimen=2, within=m.TX_LINES*m.PERIODS,
        initialize=lambda mod:
        join_sets(mod, getattr(d, tx_capacity_type_operational_period_sets),),
    )  # assumes capacity types model components are already added!

    m.TX_LINES_OPR_IN_PRD = Set(
        m.PERIODS,
        initialize=lambda mod, period:
        set(tx for (tx, p) in mod.TX_OPR_PRDS if p == period)
    )

    m.OPR_PRDS_BY_TX_LINE = Set(
        m.TX_LINES,
        initialize=lambda mod, tx:
        set(p for (l, p) in mod.TX_OPR_PRDS if l == tx)
    )

    m.TX_OPR_TMPS = Set(
        dimen=2,
        initialize=lambda mod: [
            (tx, tmp) for tx in mod.TX_LINES
            for p in mod.OPR_PRDS_BY_TX_LINE[tx]
            for tmp in mod.TMPS_IN_PRD[p]
        ]
    )

    m.TX_LINES_OPR_IN_TMP = Set(
        m.TMPS,
        initialize=lambda mod, tmp:
        set(tx for (tx, t) in mod.TX_OPR_TMPS if t == tmp)
    )

    # Expressions
    ###########################################################################

    def tx_min_capacity_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type]. \
            min_transmission_capacity_rule(mod, tx, p)

    def tx_max_capacity_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type]. \
            max_transmission_capacity_rule(mod, tx, p)

    def tx_capacity_cost_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type].\
            tx_capacity_cost_rule(mod, tx, p) \
            * mod.hours_in_subproblem_period[p] \
            / mod.hours_in_full_period[p]

    m.Tx_Min_Capacity_MW = Expression(
        m.TX_OPR_PRDS,
        rule=tx_min_capacity_rule
    )

    m.Tx_Max_Capacity_MW = Expression(
        m.TX_OPR_PRDS,
        rule=tx_max_capacity_rule
    )

    m.Tx_Capacity_Cost_in_Prd = Expression(
        m.TX_OPR_PRDS,
        rule=tx_capacity_cost_rule
    )


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
        os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                     "transmission_lines.tab"),
        sep="\t",
        usecols=["TRANSMISSION_LINES", "tx_capacity_type",
                 "tx_operational_type"]
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
        if hasattr(imported_tx_capacity_modules[op_m],
                   "load_module_specific_data"):
            imported_tx_capacity_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, subproblem, stage)
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
        os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                     "transmission_lines.tab"),
        sep="\t",
        usecols=["TRANSMISSION_LINES", "tx_capacity_type",
                 "tx_operational_type"]
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
        if hasattr(imported_tx_capacity_modules[op_m],
                   "export_module_specific_results"):
            imported_tx_capacity_modules[op_m].export_module_specific_results(
                m, d, scenario_directory, subproblem, stage
            )
        else:
            pass

    # Export transmission capacity
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "transmission_capacity.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tx_line", "period", "load_zone_from", "load_zone_to",
                         "transmission_min_capacity_mw",
                         "transmission_max_capacity_mw"])
        for (tx_line, p) in m.TX_OPR_PRDS:
            writer.writerow([
                tx_line,
                p,
                m.load_zone_from[tx_line],
                m.load_zone_to[tx_line],
                value(m.Tx_Min_Capacity_MW[tx_line, p]),
                value(m.Tx_Max_Capacity_MW[tx_line, p])
            ])

    # Export transmission capacity costs
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
              "costs_transmission_capacity.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["tx_line", "period", "hours_in_full_period",
             "hours_in_subproblem_period", "load_zone_from",
             "load_zone_to", "capacity_cost"]
        )
        for (l, p) in m.TX_OPR_PRDS:
            writer.writerow([
                l,
                p,
                m.hours_in_full_period[p],
                m.hours_in_subproblem_period[p],
                m.load_zone_from[l],
                m.load_zone_to[l],
                value(m.Tx_Capacity_Cost_in_Prd[l, p])
            ])


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
        conn=db, cursor=c,
        table="results_transmission_capacity",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "transmission_capacity.csv"),
              "r") as capacity_costs_file:
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
                (scenario_id, tx_line, period, subproblem, stage,
                 load_zone_from, load_zone_to, min_mw, max_mw)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_transmission_capacity{}
            (scenario_id, tx_line, period, subproblem_id, stage_id,
            load_zone_from, load_zone_to,
            min_mw, max_mw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """.format(scenario_id)
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
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

    # Capacity cost results
    if not quiet:
        print("transmission capacity costs")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_transmission_costs_capacity",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "costs_transmission_capacity.csv"),
              "r") as capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        next(reader)  # skip header
        for row in reader:
            tx_line = row[0]
            period = row[1]
            hours_in_full_period = row[2]
            hours_in_subproblem_period = row[3]
            load_zone_from = row[4]
            load_zone_to = row[5]
            capacity_cost = row[6]
            
            results.append(
                (scenario_id, tx_line, period, subproblem, stage,
                 hours_in_full_period, hours_in_subproblem_period,
                 load_zone_from, load_zone_to, capacity_cost)
            )

    insert_temp_sql = """
        INSERT INTO  temp_results_transmission_costs_capacity{}
        (scenario_id, tx_line, period, subproblem_id, stage_id,
        hours_in_full_period, hours_in_subproblem_period,
        load_zone_from, load_zone_to, capacity_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_costs_capacity
        (scenario_id, tx_line, period, subproblem_id, stage_id, 
        hours_in_full_period, hours_in_subproblem_period,
        load_zone_from, load_zone_to, capacity_cost)
        SELECT
        scenario_id, tx_line, period, subproblem_id, stage_id,
        hours_in_full_period, hours_in_subproblem_period, 
        load_zone_from, load_zone_to, capacity_cost
        FROM temp_results_transmission_costs_capacity{}
         ORDER BY scenario_id, tx_line, period, subproblem_id, stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


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
    spin_on_database_lock(conn=db, cursor=c, sql=del_sql,
                          data=(scenario_id,),
                          many=False)

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

    spin_on_database_lock(conn=db, cursor=c, sql=agg_sql,
                          data=(scenario_id,),
                          many=False)

