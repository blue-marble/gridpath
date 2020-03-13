#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a Tx-line-level module that adds to the formulation components that
describe the operations-related costs of transmission lines, namely hurdle
rate costs. Hurdle rate costs are currently applied on power sent across the
transmission line.
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
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`hurdle_rate_pos_dir_per_mwh`                                   |
    | | *Defined over*: :code:`TX_OPR_PRDS`                                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defaults to*: :code:`0`                                              |
    |                                                                         |
    | The transmission line's hurdle rate in $ per MWh for its positive       |
    | flows in each operational period.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`hurdle_rate_neg_dir_per_mwh`                                   |
    | | *Defined over*: :code:`TX_OPR_PRDS`                                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defaults to*: :code:`0`                                              |
    |                                                                         |
    | The transmission line's hurdle rate in $ per MWh for its negative       |
    | flows (i.e. against the line's defined direction) in each operational   |
    | period.                                                                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`Hurdle_Cost_Pos_Dir`                                           |
    | | *Defined over*: :code:`TX_OPR_TMPS`                                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission line's hurdle costs in $ for its positive flows in     |
    | in each operational period.                                             |
    +-------------------------------------------------------------------------+
    | | :code:`Hurdle_Cost_Neg_Dir`                                           |
    | | *Defined over*: :code:`TX_OPR_TMPS`                                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission line's hurdle costs in $ for its negative flows        |
    | (i.e. against the line's defined direction) in each operational         |
    | timepoint.                                                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`Hurdle_Cost_Pos_Dir_Constraint`                                |
    | | *Enforced over*: :code:`TX_OPR_TMPS`                                  |
    |                                                                         |
    | The transmission line's positive direction hurdle cost should be larger |
    | than or equal to the line's hurdle rate multiplied by its transmission  |
    | flow in each operational timepoint. When line flows are negative, this  |
    | will set the the cost to zero.                                          |
    +-------------------------------------------------------------------------+
    | | :code:`Hurdle_Cost_Neg_Dir_Constraint`                                |
    | | *Enforced over*: :code:`TX_OPR_TMPS`                                  |
    |                                                                         |
    | The transmission line's negative direction hurdle cost should be larger |
    | than or equal to the line's hurdle rate multiplied by its negative      |
    | transmission flow in each operational timepoint. When line flows are    |
    | positive, this will set the cost to zero.                               |
    +-------------------------------------------------------------------------+


    """

    # Optional Input Params
    ###########################################################################

    m.hurdle_rate_pos_dir_per_mwh = Param(
        m.TX_LINES, m.PERIODS,  # TODO: chanage to TX_OPR_PRDS?
        within=NonNegativeReals,
        default=0
    )

    m.hurdle_rate_neg_dir_per_mwh = Param(
        m.TX_LINES, m.PERIODS,  # TODO: chanage to TX_OPR_PRDS?
        within=NonNegativeReals,
        default=0
    )

    # Variables
    ###########################################################################

    m.Hurdle_Cost_Pos_Dir = Var(
        m.TX_OPR_TMPS,
        within=NonNegativeReals
    )
    m.Hurdle_Cost_Neg_Dir = Var(
        m.TX_OPR_TMPS,
        within=NonNegativeReals
    )

    # Constraints
    ###########################################################################

    m.Hurdle_Cost_Pos_Dir_Constraint = Constraint(
        m.TX_OPR_TMPS,
        rule=hurdle_cost_pos_dir_rule
    )

    m.Hurdle_Cost_Neg_Dir_Constraint = Constraint(
        m.TX_OPR_TMPS,
        rule=hurdle_cost_neg_dir_rule
    )


# Constraint Formulation Rules
###############################################################################

def hurdle_cost_pos_dir_rule(mod, tx, tmp):
    """
    **Constraint Name**: Hurdle_Cost_Pos_Dir_Constraint
    **Enforced Over**: TX_OPR_TMPS

    Hurdle_Cost_Pos_Dir must be non-negative, so will be 0
    when Transmit_Power is negative (flow in the negative direction).
    """
    if mod.hurdle_rate_pos_dir_per_mwh[tx, mod.period[tmp]] \
            == 0:
        return Constraint.Skip
    else:
        return mod.Hurdle_Cost_Pos_Dir[tx, tmp] \
            >= mod.Transmit_Power_MW[tx, tmp] \
            * mod.hurdle_rate_pos_dir_per_mwh[tx, mod.period[tmp]]


def hurdle_cost_neg_dir_rule(mod, tx, tmp):
    """
    **Constraint Name**: Hurdle_Cost_Neg_Dir_Constraint
    **Enforced Over**: TX_OPR_TMPS

    Hurdle_Cost_Neg_Dir must be non-negative, so will be 0
    when Transmit_Power is positive (flow in the positive direction).
    """
    if mod.hurdle_rate_neg_dir_per_mwh[tx, mod.period[tmp]] \
            == 0:
        return Constraint.Skip
    else:
        return mod.Hurdle_Cost_Neg_Dir[tx, tmp] \
            >= -mod.Transmit_Power_MW[tx, tmp] \
            * mod.hurdle_rate_neg_dir_per_mwh[tx, mod.period[tmp]]


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
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "transmission_hurdle_rates.tab"),
        select=("transmission_line", "period",
                "hurdle_rate_positive_direction_per_mwh",
                "hurdle_rate_negative_direction_per_mwh"),
        param=(m.hurdle_rate_pos_dir_per_mwh,
               m.hurdle_rate_neg_dir_per_mwh)
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export transmission operational cost results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m: The Pyomo abstract model
    :param d: Dynamic components
    :return: Nothing
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
        for (tx, tmp) in m.TX_OPR_TMPS:
            writer.writerow([
                tx,
                m.period[tmp],
                tmp,
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.load_zone_from[tx],
                m.load_zone_to[tx],
                value(m.Hurdle_Cost_Pos_Dir[tx, tmp]),
                value(m.Hurdle_Cost_Neg_Dir[tx, tmp])
            ])


# Database
###############################################################################

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


def write_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
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

    with open(os.path.join(inputs_directory, "transmission_hurdle_rates.tab"),
              "w", newline="") as sim_flows_file:
        writer = csv.writer(sim_flows_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["transmission_line", "period",
             "hurdle_rate_positive_direction_per_mwh",
             "hurdle_rate_negative_direction_per_mwh"]
        )

        for row in hurdle_rates:
            writer.writerow(row)


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
    # Hurdle costs
    if not quiet:
        print("transmission hurdle costs")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_transmission_hurdle_costs",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, "costs_transmission_hurdle.csv"),
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


# Validation
###############################################################################

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
