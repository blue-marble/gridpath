#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module, aggregates the net power flow in/out of a load zone on all
transmission lines connected to the load zone to create a load-balance
production component, and adds it to the load-balance constraint.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import \
    load_balance_production_components, load_balance_consumption_components


def add_model_components(m, d):
    """
    Add net transmitted power to load balance
    :param m:
    :param d:
    :return:
    """

    def total_transmission_to_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in
                   mod.TRANSMISSION_LINES_OPERATIONAL_IN_TIMEPOINT[tmp]
                   if mod.load_zone_to[tx] == z)
    m.Transmission_to_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                           rule=total_transmission_to_rule)
    getattr(d, load_balance_production_components).append(
        "Transmission_to_Zone_MW"
    )

    def total_transmission_from_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in
                   mod.TRANSMISSION_LINES_OPERATIONAL_IN_TIMEPOINT[tmp]
                   if mod.load_zone_from[tx] == z)
    m.Transmission_from_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                             rule=total_transmission_from_rule)
    getattr(d, load_balance_consumption_components).append(
        "Transmission_from_Zone_MW"
    )


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export zone-level imports and exports
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "imports_exports.csv"), "w") as imp_exp_file:
        writer = csv.writer(imp_exp_file)
        writer.writerow(
            ["load_zone", "timepoint", "period", "horizon", "horizon_weight",
             "number_of_hours_in_timepoint",
             "imports_mw", "exports_mw", "net_imports_mw"]
        )
        for z in m.LOAD_ZONES:
            for tmp in m.TIMEPOINTS:
                writer.writerow([
                    z,
                    tmp,
                    m.period[tmp],
                    m.horizon[tmp],
                    m.horizon_weight[m.horizon[tmp]],
                    m.number_of_hours_in_timepoint[tmp],
                    value(m.Transmission_to_Zone_MW[z, tmp]),
                    value(m.Transmission_from_Zone_MW[z, tmp]),
                    (value(m.Transmission_to_Zone_MW[z, tmp]) -
                        value(m.Transmission_from_Zone_MW[z, tmp]))
                ])


def import_results_into_database(scenario_id, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("imports and exports")
    c.execute(
        """DELETE FROM results_transmission_imports_exports
        WHERE scenario_id = {};""".format(scenario_id)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_transmission_imports_exports"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_transmission_imports_exports"""
        + str(scenario_id) + """(
            scenario_id INTEGER,
            load_zone VARCHAR(64),
            period INTEGER,
            horizon INTEGER,
            timepoint INTEGER,
            horizon_weight FLOAT,
            number_of_hours_in_timepoint FLOAT,
            imports_mw FLOAT,
            exports_mw FLOAT,
            net_imports_mw FLOAT,
            PRIMARY KEY (scenario_id, load_zone, timepoint)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "imports_exports.csv"),
              "r") as tx_op_file:
        reader = csv.reader(tx_op_file)

        next(reader)  # skip header
        for row in reader:
            load_zone = row[0]
            timepoint = row[1]
            period = row[2]
            horizon = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            imports_mw = row[6]
            exports_mw = row[7]
            net_imports_mw = row[8]
            c.execute(
                """INSERT INTO temp_results_transmission_imports_exports"""
                + str(scenario_id) + """
                    (scenario_id, load_zone, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    imports_mw, exports_mw, net_imports_mw)
                    VALUES ({}, '{}', {}, {}, {}, {}, {},'{}', '{}',
                    {});""".format(
                    scenario_id, load_zone, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    imports_mw, exports_mw, net_imports_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_transmission_imports_exports
        (scenario_id, load_zone, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        imports_mw, exports_mw, net_imports_mw)
        SELECT
        scenario_id, load_zone, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        imports_mw, exports_mw, net_imports_mw
        FROM temp_results_transmission_imports_exports""" + str(scenario_id) + """
            ORDER BY scenario_id, load_zone, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_transmission_imports_exports"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
