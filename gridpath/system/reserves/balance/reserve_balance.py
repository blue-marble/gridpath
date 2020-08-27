#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from builtins import next
import csv
import os.path
from pyomo.environ import Var, Constraint, NonNegativeReals, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import


def generic_add_model_components(
        m,
        d,
        reserve_zone_set,
        reserve_violation_variable,
        reserve_violation_expression,
        reserve_violation_allowed_param,
        reserve_requirement_expression,
        total_reserve_provision_expression,
        meet_reserve_constraint,
):
    """
    Ensure reserves are balanced
    :param m:
    :param d:
    :param reserve_zone_set:
    :param reserve_violation_variable:
    :param reserve_violation_expression:
    :param reserve_violation_allowed_param:
    :param reserve_requirement_expression:
    :param total_reserve_provision_expression:
    :param meet_reserve_constraint:
    :return:
    """

    # Penalty for violation
    setattr(m, reserve_violation_variable,
            Var(getattr(m, reserve_zone_set), m.TMPS,
                within=NonNegativeReals)
            )

    def violation_expression_rule(mod, ba, tmp):
        """

        :param mod:
        :param ba:
        :param tmp:
        :return:
        """
        return getattr(mod, reserve_violation_allowed_param)[ba] \
            * getattr(mod, reserve_violation_variable)[ba, tmp]

    setattr(m, reserve_violation_expression,
            Expression(getattr(m, reserve_zone_set), m.TMPS,
                       rule=violation_expression_rule))

    # Reserve constraints
    def meet_reserve_rule(mod, ba, tmp):
        return getattr(mod, total_reserve_provision_expression)[ba, tmp] \
            + getattr(mod, reserve_violation_expression)[ba, tmp] \
            == getattr(mod, reserve_requirement_expression)[ba, tmp]

    setattr(m, meet_reserve_constraint,
            Constraint(getattr(m, reserve_zone_set), m.TMPS,
                       rule=meet_reserve_rule))


def generic_export_results(scenario_directory, subproblem, stage, m, d,
                           filename,
                           column_name,
                           reserve_zone_set,
                           reserve_violation_expression
                           ):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :param filename:
    :param column_name:
    :param reserve_zone_set:
    :param reserve_violation_expression:
    :return:
    """
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           filename), "w", newline="") \
            as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["ba", "period", "timepoint",
                         "discount_factor", "number_years_represented",
                         "timepoint_weight", "number_of_hours_in_timepoint",
                         "spinup_or_lookahead", column_name]
                        )
        for (ba, tmp) in getattr(m, reserve_zone_set) * m.TMPS:
            writer.writerow([
                ba,
                m.period[tmp],
                tmp,
                m.discount_factor[m.period[tmp]],
                m.number_years_represented[m.period[tmp]],
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.spinup_or_lookahead[tmp],
                value(getattr(m, reserve_violation_expression)[ba, tmp])
            ]
            )


def generic_save_duals(m, reserve_constraint_name):
    """

    :param m:
    :param reserve_constraint_name:
    :return:
    """
    m.constraint_indices[reserve_constraint_name] = \
        ["zone", "timepoint", "dual"]


def generic_import_results_to_database(scenario_id, subproblem, stage,
                                       c, db, results_directory, reserve_type):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param reserve_type:
    :return:
    """

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_system_{}_balance""".format(reserve_type),
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           reserve_type + "_violation.csv"),
              "r") as violation_file:
        reader = csv.reader(violation_file)

        next(reader)  # skip header
        for row in reader:
            ba = row[0]
            period = row[1]
            timepoint = row[2]
            discount_factor = row[3]
            number_years_represented = row[4]
            timepoint_weight = row[5]
            number_of_hours_in_timepoint = row[6]
            spinup_or_lookahead = row[7]
            violation = row[8]

            results.append(
                (scenario_id, ba, period,
                 subproblem, stage, timepoint,
                 discount_factor, number_years_represented, timepoint_weight,
                 number_of_hours_in_timepoint, spinup_or_lookahead, violation)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_system_{}_balance{}
        (scenario_id, {}_ba, period,
        subproblem_id, stage_id, timepoint, 
        discount_factor, number_years_represented, timepoint_weight, 
        number_of_hours_in_timepoint, spinup_or_lookahead,
        violation_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(reserve_type, scenario_id, reserve_type)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_{}_balance
        (scenario_id, {}_ba, period, 
        subproblem_id, stage_id, timepoint,
        discount_factor, number_years_represented, timepoint_weight, 
        spinup_or_lookahead, number_of_hours_in_timepoint, violation_mw)
        SELECT
        scenario_id, {}_ba, period, 
        subproblem_id, stage_id, timepoint,
        discount_factor, number_years_represented, timepoint_weight, 
        number_of_hours_in_timepoint, spinup_or_lookahead, violation_mw
        FROM temp_results_system_{}_balance{}
        ORDER BY scenario_id, {}_ba, 
        subproblem_id, stage_id, timepoint;
        """.format(reserve_type, reserve_type, reserve_type, reserve_type,
                   scenario_id, reserve_type)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

    # Update duals
    dual_files = {
        "lf_reserves_up": "Meet_LF_Reserves_Up_Constraint.csv",
        "lf_reserves_down": "Meet_LF_Reserves_Down_Constraint.csv",
        "regulation_up": "Meet_Regulation_Up_Constraint.csv",
        "regulation_down": "Meet_Regulation_Down_Constraint.csv",
        "frequency_response": "Meet_Frequency_Response_Constraint.csv",
        "frequency_response_partial":
            "Meet_Frequency_Response_Partial_Constraint.csv",
        "spinning_reserves": "Meet_Spinning_Reserves_Constraint.csv"
    }

    duals_results = []
    with open(os.path.join(results_directory, dual_files[reserve_type]),
              "r") as reserve_balance_duals_file:
        reader = csv.reader(reserve_balance_duals_file)

        next(reader)  # skip header

        for row in reader:
            duals_results.append(
                (row[2], row[0], row[1], scenario_id, subproblem, stage)
            )

    duals_sql = """
        UPDATE results_system_{}_balance
        SET dual = ?
        WHERE {}_ba = ?
        AND timepoint = ?
        AND scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(reserve_type, reserve_type)

    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal cost per MW
    mc_sql = """
        UPDATE results_system_{}_balance
        SET marginal_price_per_mw = 
        dual / (discount_factor * number_years_represented * timepoint_weight 
        * number_of_hours_in_timepoint)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(reserve_type)
    spin_on_database_lock(conn=db, cursor=c, sql=mc_sql,
                          data=(scenario_id, subproblem, stage),
                          many=False)
