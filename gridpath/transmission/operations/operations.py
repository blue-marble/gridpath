#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a line-level module that adds to the formulation components that
describe the amount of power flowing on each line.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.auxiliary import load_tx_operational_type_modules
from gridpath.auxiliary.dynamic_components import \
    required_tx_operational_modules


def add_model_components(m, d):
    """
    :param m:
    :param d:
    :return:
    """

    # Import needed transmission operational type modules
    imported_tx_operational_modules = load_tx_operational_type_modules(
            getattr(d, required_tx_operational_modules))

    # TODO: should we add the module specific components here or in
    #  capacity_types/__init__.py? Doing it in __init__.py to be consistent with
    #  projects/operations/power.py
    # Get transmitted power for all lines from the tx operational modules
    def transmit_power_rule(mod, tx, tmp):
        tx_op_type = mod.tx_operational_type[tx]
        return imported_tx_operational_modules[tx_op_type].\
            transmit_power_rule(mod, tx, tmp)

    m.Transmit_Power_MW = Expression(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=transmit_power_rule
    )


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
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "transmission_operations.csv"), "w", newline="") as \
            tx_op_results_file:
        writer = csv.writer(tx_op_results_file)
        writer.writerow(["tx_line", "lz_from", "lz_to", "timepoint", "period",
                         "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "transmission_flow_mw"])
        for (l, tmp) in m.TRANSMISSION_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                l,
                m.load_zone_from[l],
                m.load_zone_to[l],
                tmp,
                m.period[tmp],
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                value(m.Transmit_Power_MW[l, tmp])
            ])

    # TODO: does this belong here or in operational_types/__init__.py?
    #  (putting it here to be in line with projects/operations/power.py)
    # Module-specific transmission operational results
    imported_tx_operational_modules = load_tx_operational_type_modules(
        getattr(d, required_tx_operational_modules))
    for op_m in getattr(d, required_tx_operational_modules):
        if hasattr(imported_tx_operational_modules[op_m],
                   "export_module_specific_results"):
            imported_tx_operational_modules[op_m].\
                export_module_specific_results(
                m, d, scenario_directory, subproblem, stage,
            )
        else:
            pass


def import_results_into_database(scenario_id, subproblem, stage, c, db,
                                 results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("transmission operations")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_transmission_operations",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, "transmission_operations.csv"),
              "r") as tx_op_file:
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
            tx_flow = row[7]

            results.append(
                (scenario_id, tx_line, period, subproblem, stage,
                 timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 lz_from, lz_to, tx_flow)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_transmission_operations{}
        (scenario_id, transmission_line, period, subproblem_id, 
        stage_id, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, transmission_flow_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_operations
        (scenario_id, transmission_line, period, subproblem_id, stage_id,
        timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, transmission_flow_mw)
        SELECT
        scenario_id, transmission_line, period, subproblem_id, stage_id,
        timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, transmission_flow_mw
        FROM temp_results_transmission_operations{}
         ORDER BY scenario_id, transmission_line, subproblem_id, stage_id, 
        timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
