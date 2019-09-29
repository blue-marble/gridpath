#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a Tx-line-level module that adds to the formulation components that
describe the operations-related costs of transmisison lines (e.g. hurdle
rate costs).
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Var, Constraint, NonNegativeReals, \
    Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.hurdle_rate_positive_direction_per_mwh = Param(
        m.TRANSMISSION_LINES, m.PERIODS,
        within=NonNegativeReals, default=0
    )

    m.hurdle_rate_negative_direction_per_mwh = Param(
        m.TRANSMISSION_LINES, m.PERIODS,
        within=NonNegativeReals, default=0
    )

    m.Hurdle_Cost_Positive_Direction = Var(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS, within=NonNegativeReals
    )
    m.Hurdle_Cost_Negative_Direction = Var(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS, within=NonNegativeReals
    )

    def hurdle_cost_positive_direction_rule(mod, tx, tmp):
        """
        Hurdle_Cost_Positive_Direction must be non-negative, so will be 0
        when Transmit_Power is negative (flow in the negative direction)
        :param mod:
        :param tx:
        :param tmp:
        :return:
        """
        if mod.hurdle_rate_positive_direction_per_mwh[tx, mod.period[tmp]] \
                == 0:
            return Constraint.Skip
        else:
            return mod.Hurdle_Cost_Positive_Direction[tx, tmp] \
                >= mod.Transmit_Power_MW[tx, tmp] * \
                mod.hurdle_rate_positive_direction_per_mwh[tx, mod.period[tmp]]
    m.Hurdle_Cost_Positive_Direction_Constraint = Constraint(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=hurdle_cost_positive_direction_rule
    )

    def hurdle_cost_negative_direction_rule(mod, tx, tmp):
        """
        Hurdle_Cost_Negative_Direction must be non-negative, so will be 0
        when Transmit_Power is positive (flow in the positive direction)
        :param mod:
        :param tx:
        :param tmp:
        :return:
        """
        if mod.hurdle_rate_negative_direction_per_mwh[tx, mod.period[tmp]] \
                == 0:
            return Constraint.Skip
        else:
            return mod.Hurdle_Cost_Negative_Direction[tx, tmp] \
                >= -mod.Transmit_Power_MW[tx, tmp] * \
                mod.hurdle_rate_negative_direction_per_mwh[tx, mod.period[tmp]]
    m.Hurdle_Cost_Negative_Direction_Constraint = Constraint(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=hurdle_cost_negative_direction_rule
    )


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
    data_portal.load(filename=os.path.join(
                        scenario_directory, subproblem, stage, "inputs",
                        "transmission_hurdle_rates.tab"),
                     select=("transmission_line", "period",
                             "hurdle_rate_positive_direction_per_mwh",
                             "hurdle_rate_negative_direction_per_mwh"),
                     param=(m.hurdle_rate_positive_direction_per_mwh,
                            m.hurdle_rate_negative_direction_per_mwh)
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    hurdle_rates = c.execute(
        """SELECT transmission_line, period, 
        hurdle_rate_positive_direction_per_mwh,
        hurdle_rate_negative_direction_per_mwh
        FROM inputs_transmission_hurdle_rates
        INNER JOIN
        (SELECT period
         FROM inputs_temporal_periods
         WHERE temporal_scenario_id = {}) as relevant_periods
         USING (period)
         WHERE transmission_hurdle_rate_scenario_id = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_HURDLE_RATE_SCENARIO_ID
        )
    )

    return hurdle_rates


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # hurdle_rates = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    transmission_hurdle_rates.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    hurdle_rates = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "transmission_hurdle_rates.tab"),
              "w", newline="") as \
            sim_flows_file:
        writer = csv.writer(sim_flows_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["transmission_line", "period",
             "hurdle_rate_positive_direction_per_mwh",
             "hurdle_rate_negative_direction_per_mwh"]
        )

        for row in hurdle_rates:
            writer.writerow(row)


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export transmission operational cost results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
              "costs_transmission_hurdle.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["tx_line", "period", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone_from", "load_zone_to",
             "hurdle_cost_positive_direction",
             "hurdle_cost_negative_direction"]
        )
        for (tx, tmp) in m.TRANSMISSION_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                tx,
                m.period[tmp],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone_from[tx],
                m.load_zone_to[tx],
                value(m.Hurdle_Cost_Positive_Direction[tx, tmp]),
                value(m.Hurdle_Cost_Negative_Direction[tx, tmp])
            ])


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # Hurdle costs
    print("transmission hurdle costs")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_transmission_hurdle_costs",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "costs_transmission_hurdle.csv"),
              "r") as tx_op_file:
        reader = csv.reader(tx_op_file)

        next(reader)  # skip header
        for row in reader:
            tx_line = row[0]
            period = row[1]
            timepoint = row[2]
            timepoint_weight = row[3]
            number_of_hours_in_timepoint = row[4]
            lz_from = row[5]
            lz_to = row[6]
            hurdle_cost_positve_direction = row[7]
            hurdle_cost_negative_direction = row[8]
            
            results.append(
                (scenario_id, tx_line, period, subproblem, stage,
                 timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 lz_from, lz_to,
                 hurdle_cost_positve_direction,
                 hurdle_cost_negative_direction)
            )
    insert_temp_sql = """
        INSERT INTO temp_results_transmission_hurdle_costs{}
        (scenario_id, transmission_line, period, subproblem_id, stage_id,
        timepoint, timepoint_weight,
        number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, 
        hurdle_cost_positive_direction, hurdle_cost_negative_direction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_hurdle_costs
        (scenario_id, transmission_line, period, subproblem_id, stage_id, 
        timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, hurdle_cost_positive_direction,
        hurdle_cost_negative_direction)
        SELECT
        scenario_id, transmission_line, period, subproblem_id, stage_id,
        timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, hurdle_cost_positive_direction,
        hurdle_cost_negative_direction
        FROM temp_results_transmission_hurdle_costs{}
         ORDER BY scenario_id, transmission_line, subproblem_id, stage_id, 
        timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
