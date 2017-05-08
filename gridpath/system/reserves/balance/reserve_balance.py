#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Var, Constraint, NonNegativeReals


def generic_add_model_components(
        m,
        d,
        reserve_zone_timepoint_set,
        reserve_violation_variable,
        reserve_requirement_param,
        total_reserve_provision_expression,
        meet_reserve_constraint,
):
    """
    Ensure reserves are balanced
    :param m:
    :param d:
    :param reserve_zone_timepoint_set:
    :param reserve_violation_variable:
    :param reserve_requirement_param:
    :param total_reserve_provision_expression:
    :param meet_reserve_constraint:
    :return:
    """

    # Penalty for violation
    setattr(m, reserve_violation_variable,
            Var(getattr(m, reserve_zone_timepoint_set),
                within=NonNegativeReals)
            )

    # Reserve constraints
    def meet_reserve_rule(mod, ba, tmp):
        return getattr(mod, total_reserve_provision_expression)[ba, tmp] \
            + getattr(mod, reserve_violation_variable)[ba, tmp] \
            == getattr(mod, reserve_requirement_param)[ba, tmp]

    setattr(m, meet_reserve_constraint,
            Constraint(getattr(m, reserve_zone_timepoint_set),
                       rule=meet_reserve_rule))


def generic_export_results(scenario_directory, horizon, stage, m, d,
                           filename,
                           column_name,
                           reserve_zone_timepoint_set,
                           reserve_violation_variable
                           ):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :param filename:
    :param column_name:
    :param reserve_zone_timepoint_set:
    :param reserve_violation_variable:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           filename), "wb") \
            as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["ba", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         column_name]
                        )
        for (ba, tmp) in getattr(m, reserve_zone_timepoint_set):
            writer.writerow([
                ba,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                getattr(m, reserve_violation_variable)[ba, tmp].value]
            )


def generic_save_duals(m, reserve_constraint_name):
    """

    :param m:
    :param reserve_constraint_name:
    :return:
    """
    m.constraint_indices[reserve_constraint_name] = \
        ["zone", "timepoint", "dual"]


def generic_import_results_to_database(
        scenario_id, c, db, results_directory,
        reserve_type
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param reserve_type:
    :return:
    """

    c.execute(
        """DELETE FROM results_system_""" + reserve_type + """_balance
        WHERE scenario_id = {};""".format(scenario_id)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_system_""" + reserve_type + """_balance"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_system_""" + reserve_type + """_balance"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        """ + reserve_type + """_ba VARCHAR(32),
        period INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        violation_mw FLOAT,
        PRIMARY KEY (scenario_id, """ + reserve_type + """_ba, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           reserve_type + "_violation.csv"),
              "r") as violation_file:
        reader = csv.reader(violation_file)

        reader.next()  # skip header
        for row in reader:
            ba = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            violation = row[6]
            c.execute(
                """INSERT INTO 
                temp_results_system_""" + reserve_type + """_balance"""
                + str(scenario_id) + """
                (scenario_id, """ + reserve_type + """_ba, period, horizon, 
                timepoint, horizon_weight, number_of_hours_in_timepoint,
                violation_mw)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, {});""".format(
                    scenario_id, ba, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    violation
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_system_""" + reserve_type + """_balance
        (scenario_id, """ + reserve_type + """_ba, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint, violation_mw)
        SELECT
        scenario_id, """ + reserve_type + """_ba, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint, violation_mw
        FROM temp_results_system_""" + reserve_type + """_balance"""
        + str(scenario_id) + """
        ORDER BY scenario_id, """ + reserve_type + """_ba, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_system_""" + reserve_type + """_balance"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
