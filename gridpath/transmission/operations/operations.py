#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Var, Constraint, Expression, Reals, value

from gridpath.auxiliary.dynamic_components import \
    load_balance_production_components, load_balance_consumption_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Define various sets to be used in transmission operations module
    m.OPERATIONAL_PERIODS_BY_TRANSMISSION_LINE = \
        Set(m.TRANSMISSION_LINES,
            rule=lambda mod, tx: set(
                p for (l, p) in mod.TRANSMISSION_OPERATIONAL_PERIODS if
                l == tx)
            )

    def tx_op_tmps_init(mod):
        tx_tmps = set()
        for tx in mod.TRANSMISSION_LINES:
            for p in mod.OPERATIONAL_PERIODS_BY_TRANSMISSION_LINE[tx]:
                for tmp in mod.TIMEPOINTS_IN_PERIOD[p]:
                    tx_tmps.add((tx, tmp))
        return tx_tmps
    m.TRANSMISSION_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, rule=tx_op_tmps_init)

    m.TRANSMISSION_LINES_OPERATIONAL_IN_TIMEPOINT = \
        Set(m.TIMEPOINTS,
            rule=lambda mod, tmp: set(
                tx for (tx, t) in mod.TRANSMISSION_OPERATIONAL_TIMEPOINTS
                if t == tmp)
            )

    m.Transmit_Power_MW = Var(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                              within=Reals)

    def min_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_MW[l, tmp] \
            >= mod.Transmission_Min_Capacity_MW[l, mod.period[tmp]]

    m.Min_Transmit_Constraint = \
        Constraint(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                   rule=min_transmit_rule)

    def max_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_MW[l, tmp] \
            <= mod.Transmission_Max_Capacity_MW[l, mod.period[tmp]]

    m.Max_Transmit_Constraint = \
        Constraint(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                   rule=max_transmit_rule)

    # Add to load balance
    def total_transmission_to_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in
                   mod.TRANSMISSION_LINES_OPERATIONAL_IN_TIMEPOINT[tmp]
                   if mod.load_zone_to[tx] == z)
    m.Transmission_to_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                           rule=total_transmission_to_rule)
    getattr(d, load_balance_production_components).append(
        "Transmission_to_Zone_MW")

    def total_transmission_from_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in
                   mod.TRANSMISSION_LINES_OPERATIONAL_IN_TIMEPOINT[tmp]
                   if mod.load_zone_from[tx] == z)
    m.Transmission_from_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                             rule=total_transmission_from_rule)
    getattr(d, load_balance_consumption_components).append(
        "Transmission_from_Zone_MW")


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export transmission operations
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "transmission_operations.csv"), "wb") as \
            tx_op_results_file:
        writer = csv.writer(tx_op_results_file)
        writer.writerow(["tx_line", "lz_from", "lz_to", "timepoint", "period",
                         "horizon", "horizon_weight", 
                         "number_of_hours_in_timepoint",
                         "transmission_flow_mw"])
        for (l, tmp) in m.TRANSMISSION_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                l,
                m.load_zone_from[l],
                m.load_zone_to[l],
                tmp,
                m.period[tmp],
                m.horizon[tmp],
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                value(m.Transmit_Power_MW[l, tmp])
            ])

    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "imports_exports.csv"), "wb") as imp_exp_file:
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
    print("transmission operations")

    c.execute(
        """DELETE FROM results_transmission_operations
        WHERE scenario_id = {};""".format(scenario_id)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_transmission_operations"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_transmission_operations""" 
        + str(scenario_id) + """(
        scenario_id INTEGER,
        transmission_line VARCHAR(64),
        period INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        load_zone_from VARCHAR(32),
        load_zone_to VARCHAR(32),
        transmission_flow_mw FLOAT,
        PRIMARY KEY (scenario_id, transmission_line, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory, "transmission_operations.csv"), 
              "r") as tx_op_file:
        reader = csv.reader(tx_op_file)

        reader.next()  # skip header
        for row in reader:
            tx_line = row[0]
            lz_from = row[1]
            lz_to = row[2]
            timepoint = row[3]
            period = row[4]
            horizon = row[5]
            horizon_weight = row[6]
            number_of_hours_in_timepoint = row[7]
            tx_flow = row[8]
            c.execute(
                """INSERT INTO temp_results_transmission_operations"""
                + str(scenario_id) + """
                (scenario_id, transmission_line, period, horizon, timepoint,
                horizon_weight, number_of_hours_in_timepoint,
                load_zone_from, load_zone_to, transmission_flow_mw)
                VALUES ({}, '{}', {}, {}, {}, {}, {},'{}', '{}',
                {});""".format(
                    scenario_id, tx_line, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    lz_from, lz_to, tx_flow
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_transmission_operations
        (scenario_id, transmission_line, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, transmission_flow_mw)
        SELECT
        scenario_id, transmission_line, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, transmission_flow_mw
        FROM temp_results_transmission_operations""" + str(scenario_id) + """
        ORDER BY scenario_id, transmission_line, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_transmission_operations"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()

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

        reader.next()  # skip header
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