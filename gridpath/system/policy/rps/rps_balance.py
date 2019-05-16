#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simplest implementation with a MWh target
"""

from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
import pandas as pd

from pyomo.environ import Constraint, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    def rps_target_rule(mod, z, p):
        """
        Total delivered RPS-eligible energy must exceed target
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return mod.Total_Delivered_RPS_Energy_MWh[z, p] \
            >= mod.rps_target_mwh[z, p]

    m.RPS_Target_Constraint = Constraint(m.RPS_ZONE_PERIODS_WITH_RPS,
                                         rule=rps_target_rule)


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "rps.csv"), "w") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["rps_zone", "period",
                         "discount_factor", "number_years_represented",
                         "rps_target_mwh",
                         "delivered_rps_energy_mwh",
                         "curtailed_rps_energy_mwh",
                         "total_rps_energy_mwh",
                         "fraction_of_rps_target_met",
                         "fraction_of_rps_energy_curtailed"])
        for (z, p) in m.RPS_ZONE_PERIODS_WITH_RPS:
            writer.writerow([
                z,
                p,
                m.discount_factor[p],
                m.number_years_represented[p],
                float(m.rps_target_mwh[z, p]),
                value(m.Total_Delivered_RPS_Energy_MWh[z, p]),
                value(m.Total_Curtailed_RPS_Energy_MWh[z, p]),
                value(m.Total_Delivered_RPS_Energy_MWh[z, p]) +
                value(m.Total_Curtailed_RPS_Energy_MWh[z, p]),
                value(m.Total_Delivered_RPS_Energy_MWh[z, p]) /
                float(m.rps_target_mwh[z, p]),
                value(m.Total_Curtailed_RPS_Energy_MWh[z, p]) /
                (value(m.Total_Delivered_RPS_Energy_MWh[z, p])
                 + value(m.Total_Curtailed_RPS_Energy_MWh[z, p]))
            ])


def save_duals(m):
    m.constraint_indices["RPS_Target_Constraint"] = \
        ["rps_zone", "period", "dual"]


def summarize_results(d, problem_directory, horizon, stage):
    """
    Summarize RPS policy results
    :param d:
    :param problem_directory:
    :param horizon:
    :param stage:
    :return:
    """

    summary_results_file = os.path.join(
        problem_directory, horizon, stage, "results", "summary_results.txt"
    )

    # Open in 'append' mode, so that results already written by other
    # modules are not overridden
    with open(summary_results_file, "a") as outfile:
        outfile.write(
            "\n### RPS RESULTS ###\n"
        )

    # All these files are small, so won't be setting indices

    # Get the main RPS results file
    rps_df = \
        pd.read_csv(os.path.join(problem_directory, horizon, stage, "results",
                                 "rps.csv")
                    )

    # Get the RPS dual results
    rps_duals_df = \
        pd.read_csv(os.path.join(problem_directory, horizon, stage, "results",
                                 "RPS_Target_Constraint.csv")
                    )

    # # Get the input metadata for periods
    # periods_df = \
    #     pd.read_csv(os.path.join(problem_directory, "inputs", "periods.tab"),
    #                 sep="\t")

    # Join the above
    results_df = pd.DataFrame(
        pd.merge(
            left=rps_df,
            right=rps_duals_df,
            how="left",
            left_on=["rps_zone", "period"],
            right_on=["rps_zone", "period"]
        )
    )

    results_df.set_index(["rps_zone", "period"], inplace=True,
                         verify_integrity=True)

    # Calculate:
    # 1) the percent of RPS energy that was curtailed
    # 2) the marginal RPS cost per MWh based on the RPS constraint duals --
    # to convert back to 'real' dollars, we need to divide by the discount
    # factor and the number of years a period represents
    results_df["percent_curtailed"] = pd.Series(index=results_df.index)
    results_df["rps_marginal_cost_per_mwh"] = pd.Series(index=results_df.index)

    pd.options.mode.chained_assignment = None  # default='warn'
    for indx, row in results_df.iterrows():
        results_df.percent_curtailed[indx] = \
            results_df.curtailed_rps_energy_mwh[indx] \
            / (results_df.delivered_rps_energy_mwh[indx] +
               results_df.curtailed_rps_energy_mwh[indx]) * 100
        results_df.rps_marginal_cost_per_mwh[indx] = \
            results_df.dual[indx] \
            / (results_df.discount_factor[indx] *
               results_df.number_years_represented[indx])

    # Set float format options
    pd.options.display.float_format = "{:,.0f}".format

    # Drop unnecessary columns before exporting
    results_df.drop("discount_factor", axis=1, inplace=True)
    results_df.drop("number_years_represented", axis=1, inplace=True)
    results_df.drop("total_rps_energy_mwh", axis=1, inplace=True)
    results_df.drop("fraction_of_rps_target_met", axis=1, inplace=True)
    results_df.drop("fraction_of_rps_energy_curtailed", axis=1, inplace=True)

    # Rearrange the columns
    cols = results_df.columns.tolist()
    cols = cols[0:3] + [cols[4]] + [cols[3]] + [cols[5]]
    results_df = results_df[cols]
    results_df.sort_index(inplace=True)
    with open(summary_results_file, "a") as outfile:
        results_df.to_string(outfile)
        outfile.write("\n")


def import_results_into_database(
        scenario_id, c, db, results_directory
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # Carbon emissions by in-zone projects
    print("system rps")
    c.execute(
        """DELETE FROM results_system_rps 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_system_rps"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_system_rps"""
        + str(scenario_id) + """(
         scenario_id INTEGER,
         rps_zone VARCHAR(64),
         period INTEGER,
         discount_factor FLOAT,
         number_years_represented FLOAT,
         rps_target_mwh FLOAT,
         delivered_rps_energy_mwh FLOAT,
         curtailed_rps_energy_mwh FLOAT,
         total_rps_energy_mwh FLOAT,
         fraction_of_rps_target_met FLOAT,
         fraction_of_rps_energy_curtailed FLOAT,
         PRIMARY KEY (scenario_id, rps_zone, period)
         );"""
    )
    db.commit()

    with open(os.path.join(results_directory,
                           "rps.csv"), "r") as \
            rps_file:
        reader = csv.reader(rps_file)

        next(reader)  # skip header
        for row in reader:
            rps_zone = row[0]
            period = row[1]
            discount_factor = row[2]
            number_years = row[3]
            rps_target = row[4]
            rps_provision = row[5]
            curtailment = row[6]
            total = row[7]
            fraction_met = row[8]
            fraction_curtailed = row[9]

            # Load results into the temporary table
            c.execute(
                """INSERT INTO 
                temp_results_system_rps"""
                + str(scenario_id) + """
                 (scenario_id, rps_zone, period, 
                 discount_factor, number_years_represented, rps_target_mwh, 
                 delivered_rps_energy_mwh, curtailed_rps_energy_mwh,
                 total_rps_energy_mwh,
                 fraction_of_rps_target_met, fraction_of_rps_energy_curtailed)
                 VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {}, {}, {}
                 );""".format(
                    scenario_id, rps_zone, period, discount_factor,
                    number_years, rps_target, rps_provision, curtailment,
                    total, fraction_met, fraction_curtailed
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_system_rps
        (scenario_id, rps_zone, period,
        discount_factor, number_years_represented, rps_target_mwh, 
        delivered_rps_energy_mwh, curtailed_rps_energy_mwh,
        total_rps_energy_mwh,
        fraction_of_rps_target_met, fraction_of_rps_energy_curtailed)
        SELECT scenario_id, rps_zone, period,
        discount_factor, number_years_represented, rps_target_mwh, 
        delivered_rps_energy_mwh, curtailed_rps_energy_mwh,
        total_rps_energy_mwh,
        fraction_of_rps_target_met, fraction_of_rps_energy_curtailed
        FROM temp_results_system_rps"""
        + str(scenario_id)
        + """
         ORDER BY scenario_id, rps_zone, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_system_rps"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()

    # Update duals
    with open(os.path.join( results_directory, "RPS_Target_Constraint.csv"),
              "r") as rps_duals_file:
        reader = csv.reader(rps_duals_file)

        next(reader)  # skip header

        for row in reader:
            c.execute(
                """UPDATE results_system_rps
                SET dual = {}
                WHERE rps_zone = '{}'
                AND period = {}
                AND scenario_id = {};""".format(
                    row[2], row[0], row[1], scenario_id
                )
            )
    db.commit()

    # Calculate marginal RPS cost per MWh
    c.execute(
        """UPDATE results_system_rps
        SET rps_marginal_cost_per_mwh = 
        dual / (discount_factor * number_years_represented)
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()
