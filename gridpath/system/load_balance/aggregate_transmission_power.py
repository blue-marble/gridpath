#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module aggregates the net power flow in/out of a load zone on all
transmission lines connected to the load zone to create a load-balance
production component, and adds it to the load-balance constraint.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.dynamic_components import \
    load_balance_production_components, load_balance_consumption_components


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """
    This method adds the transmission to/from to the load balance dynamic
    components.
    :param d:
    :return:
    """

    getattr(d, load_balance_production_components).append(
        "Transmission_to_Zone_MW"
    )

    getattr(d, load_balance_consumption_components).append(
        "Transmission_from_Zone_MW"
    )


def add_model_components(m, d):
    """
    Add net transmitted power to load balance
    :param m:
    :param d:
    :return:
    """

    def total_transmission_to_rule(mod, z, tmp):
        """
        For each load zone, iterate over the transmission lines with the
        load zone as destination to determine net imports into the load zone
        minus any losses incurred. Tx_Losses_LZ_To_MW is positive when
        Transmit_Power_MW is positive (losses are accounted for when the
        transmission flow is to the destination load zone) and 0 otherwise.
        """
        return sum(
            (mod.Transmit_Power_MW[tx, tmp]
             - mod.Tx_Losses_LZ_To_MW[tx, tmp])
            for tx in mod.TX_LINES_OPR_IN_TMP[tmp]
            if mod.load_zone_to[tx] == z
        )
    m.Transmission_to_Zone_MW = Expression(m.LOAD_ZONES, m.TMPS,
                                           rule=total_transmission_to_rule)

    def total_transmission_from_rule(mod, z, tmp):
        """
        For each load zone, iterate over the transmission lines with the
        load zone as origin to determine net exports from the load zone
        minus any losses incurred. Tx_Losses_LZ_From_MW is positive when
        Transmit_Power_MW is negative (losses are accounted for when the
        transmission flow is to the origin load zone) and 0 otherwise.
        """
        return sum(
            (mod.Transmit_Power_MW[tx, tmp]
             + mod.Tx_Losses_LZ_From_MW[tx, tmp])
            for tx in mod.TX_LINES_OPR_IN_TMP[tmp]
            if mod.load_zone_from[tx] == z
        )
    m.Transmission_from_Zone_MW = Expression(m.LOAD_ZONES, m.TMPS,
                                             rule=total_transmission_from_rule)


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export zone-level imports and exports
    :param scenario_directory:
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "imports_exports.csv"), "w", newline="") as imp_exp_file:
        writer = csv.writer(imp_exp_file)
        writer.writerow(
            ["load_zone", "timepoint", "period", "timepoint_weight",
             "number_of_hours_in_timepoint",
             "imports_mw", "exports_mw", "net_imports_mw"]
        )
        for z in m.LOAD_ZONES:
            for tmp in m.TMPS:
                writer.writerow([
                    z,
                    tmp,
                    m.period[tmp],
                    m.tmp_weight[tmp],
                    m.hrs_in_tmp[tmp],
                    value(m.Transmission_to_Zone_MW[z, tmp]),
                    value(m.Transmission_from_Zone_MW[z, tmp]),
                    (value(m.Transmission_to_Zone_MW[z, tmp]) -
                        value(m.Transmission_from_Zone_MW[z, tmp]))
                ])


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
    if not quiet:
        print("imports and exports")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_transmission_imports_exports",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )
    
    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "imports_exports.csv"),
              "r") as tx_op_file:
        reader = csv.reader(tx_op_file)

        next(reader)  # skip header
        for row in reader:
            load_zone = row[0]
            timepoint = row[1]
            period = row[2]
            timepoint_weight = row[3]
            number_of_hours_in_timepoint = row[4]
            imports_mw = row[5]
            exports_mw = row[6]
            net_imports_mw = row[7]
            
            results.append(
                (scenario_id, load_zone, period, subproblem, stage,
                 timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 imports_mw, exports_mw, net_imports_mw)
            )
            
    insert_temp_sql = """
        INSERT INTO temp_results_transmission_imports_exports{}
        (scenario_id, load_zone, period, subproblem_id, stage_id, 
        timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, 
        imports_mw, exports_mw, net_imports_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_imports_exports
        (scenario_id, load_zone, period, subproblem_id, stage_id, 
        timepoint, timepoint_weight, number_of_hours_in_timepoint,
        imports_mw, exports_mw, net_imports_mw)
        SELECT
        scenario_id, load_zone, period, subproblem_id, stage_id, 
        timepoint, timepoint_weight, number_of_hours_in_timepoint,
        imports_mw, exports_mw, net_imports_mw
        FROM temp_results_transmission_imports_exports{}
        ORDER BY scenario_id, load_zone, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
