#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a line-level module that adds to the formulation components that
describe the capacity of Tx lines that are available to the optimization for
each period. For example, the capacity can be a fixed number or an
expression with variables depending on the line's *capacity_type*. The
project capacity can then be used to constrain operations, contribute to
reliability constraints, etc.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
from functools import reduce
import os.path
from pyomo.environ import Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import load_tx_capacity_type_modules, \
    setup_results_import
from gridpath.auxiliary.dynamic_components import required_tx_capacity_modules, \
    total_cost_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed transmission capacity type modules
    imported_tx_capacity_modules = \
        load_tx_capacity_type_modules(getattr(d, required_tx_capacity_modules))
    # First, add any components specific to the transmission capacity modules
    for op_m in getattr(d, required_tx_capacity_modules):
        imp_op_m = imported_tx_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    def join_tx_cap_type_operational_period_sets(mod):
        """
        Join the sets we need to make the TRANSMISSION_OPERATIONAL_PERIODS
        super set; if list contains only a single set, return just that set
        :param mod:
        :return:
        """
        if len(mod.tx_capacity_type_operational_period_sets) == 0:
            return []
        elif len(mod.tx_capacity_type_operational_period_sets) == 1:
            return getattr(mod, mod.tx_capacity_type_operational_period_sets[0])

        else:
            return reduce(lambda x, y: getattr(mod, x) | getattr(mod, y),
                          mod.tx_capacity_type_operational_period_sets)

    m.TRANSMISSION_OPERATIONAL_PERIODS = \
        Set(dimen=2, within=m.TRANSMISSION_LINES*m.PERIODS,
            initialize=join_tx_cap_type_operational_period_sets)

    def transmission_min_capacity_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type]. \
            min_transmission_capacity_rule(mod, tx, p)

    m.Transmission_Min_Capacity_MW = \
        Expression(m.TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=transmission_min_capacity_rule)

    def transmission_max_capacity_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type]. \
            max_transmission_capacity_rule(mod, tx, p)

    m.Transmission_Max_Capacity_MW = \
        Expression(m.TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=transmission_max_capacity_rule)

    # Add costs to objective function
    def tx_capacity_cost_rule(mod, tx, p):
        """
        Get capacity cost from each line's respective capacity module
        :param mod:
        :param g:
        :param p:
        :return:
        """
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type].\
            tx_capacity_cost_rule(mod, tx, p)
    m.Transmission_Capacity_Cost_in_Period = \
        Expression(m.TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=tx_capacity_cost_rule)

    # Add costs to objective function
    def total_tx_capacity_cost_rule(mod):
        return sum(mod.Transmission_Capacity_Cost_in_Period[g, p]
                   * mod.discount_factor[p]
                   * mod.number_years_represented[p]
                   for (g, p) in mod.TRANSMISSION_OPERATIONAL_PERIODS)
    m.Total_Tx_Capacity_Costs = Expression(rule=total_tx_capacity_cost_rule)
    getattr(d, total_cost_components).append("Total_Tx_Capacity_Costs")


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
    imported_tx_capacity_modules = \
        load_tx_capacity_type_modules(getattr(d, required_tx_capacity_modules))
    for op_m in getattr(d, required_tx_capacity_modules):
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

    # Module-specific results
    imported_tx_capacity_modules = \
        load_tx_capacity_type_modules(getattr(d, required_tx_capacity_modules))
    for op_m in getattr(d, required_tx_capacity_modules):
        if hasattr(imported_tx_capacity_modules[op_m],
                   "export_module_specific_results"):
            imported_tx_capacity_modules[op_m].export_module_specific_results(
                m, d, scenario_directory, subproblem, stage
            )
        else:
            pass

    # Export transmission capacity
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "transmission_capacity.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tx_line", "period", "load_zone_from", "load_zone_to",
                         "transmission_min_capacity_mw",
                         "transmission_max_capacity_mw"])
        for (tx_line, p) in m.TRANSMISSION_OPERATIONAL_PERIODS:
            writer.writerow([
                tx_line,
                p,
                m.load_zone_from[tx_line],
                m.load_zone_to[tx_line],
                value(m.Transmission_Min_Capacity_MW[tx_line, p]),
                value(m.Transmission_Max_Capacity_MW[tx_line, p])
            ])

    # Export transmission capacity costs
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
              "costs_transmission_capacity.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["tx_line", "period", "load_zone_from",
             "load_zone_to", "annualized_capacity_cost"]
        )
        for (l, p) in m.TRANSMISSION_OPERATIONAL_PERIODS:
            writer.writerow([
                l,
                p,
                m.load_zone_from[l],
                m.load_zone_to[l],
                value(m.Transmission_Capacity_Cost_in_Period[l, p])
            ])


def import_results_into_database(scenario_id, subproblem, stage,
                                 c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # Tx capacity results
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
                           "transmission_capacity.csv"), "r") as \
            capacity_costs_file:
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
                           "costs_transmission_capacity.csv"), "r") as \
            capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        next(reader)  # skip header
        for row in reader:
            tx_line = row[0]
            period = row[1]
            load_zone_from = row[2]
            load_zone_to = row[3]
            annualized_capacity_cost = row[4]
            
            results.append(
                (scenario_id, tx_line, period, subproblem, stage,
                 load_zone_from, load_zone_to, annualized_capacity_cost)
            )

    insert_temp_sql = """
        INSERT INTO  temp_results_transmission_costs_capacity{}
        (scenario_id, tx_line, period, subproblem_id, stage_id,
        load_zone_from, load_zone_to, annualized_capacity_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_costs_capacity
        (scenario_id, tx_line, period, subproblem_id, stage_id, 
        load_zone_from, load_zone_to, annualized_capacity_cost)
        SELECT
        scenario_id, tx_line, period, subproblem_id, stage_id, 
        load_zone_from, load_zone_to, annualized_capacity_cost
        FROM temp_results_transmission_costs_capacity{}
         ORDER BY scenario_id, tx_line, period, subproblem_id, stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
