#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get the dispatch of all projects and aggregate for load balance
"""
import csv
import os.path
import pandas as pd
from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import \
    required_operational_modules, load_balance_production_components
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Get dispatch for all generators from the generator's operational module
    def power_provision_rule(mod, g, tmp):
        """
        Power provision is a variable for some generators, but not others; get
        the appropriate expression for each generator based on its operational
        type.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            power_provision_rule(mod, g, tmp)
    m.Power_Provision_MW = Expression(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                      rule=power_provision_rule)

    # Add power generation to load balance constraint
    def total_power_production_rule(mod, z, tmp):
        return sum(mod.Power_Provision_MW[g, tmp]
                   for g in mod.OPERATIONAL_PROJECTS_IN_TIMEPOINT[tmp]
                   if mod.load_zone[g] == z)
    m.Power_Production_in_Zone_MW = \
        Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                   rule=total_power_production_rule)
    getattr(d, load_balance_production_components).append(
        "Power_Production_in_Zone_MW")


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """

    # First power
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "dispatch_all.csv"), "wb") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "load_zone", "technology", "power_mw"])
        for (p, tmp) in m.PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.Power_Provision_MW[p, tmp])
            ])


def summarize_results(d, problem_directory, horizon, stage):
    """
    Summarize operational results
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
            "\n### OPERATIONAL RESULTS ###\n"
        )

    # Next, our goal is to get a summary table of power production by load
    # zone, technology, and period

    # Get the results CSV as dataframe
    operational_results_df = \
        pd.read_csv(os.path.join(problem_directory, horizon,
                                 stage, "results", "dispatch_all.csv")
                    )

    operational_results_df["weighted_power_mwh"] = \
        operational_results_df["power_mw"] * \
        operational_results_df["horizon_weight"]

    # Aggregate total power results by load_zone, technology, and period
    operational_results_agg_df = pd.DataFrame(
        operational_results_df.groupby(by=["load_zone", "period",
                                           "technology",],
                                       as_index=True
                                       ).sum()["weighted_power_mwh"]
    )

    operational_results_agg_df.columns = ["weighted_power_mwh"]

    # Aggregate total power by load_zone and period -- we'll need this
    # to find the percentage of total power by technology (for each load
    # zone and period)
    lz_period_power_df = pd.DataFrame(
        operational_results_df.groupby(by=["load_zone", "period"],
                                       as_index=True
                                       ).sum()["weighted_power_mwh"]
    )

    # Name the power column
    operational_results_agg_df.columns = ["weighted_power_mwh"]
    # Add a column with the percentage of total power by load zone and tech
    operational_results_agg_df["percent_total_power"] = pd.Series(
        index=operational_results_agg_df.index
    )

    # Calculate the percent of total power for each tech (by load zone
    # and period)
    for indx, row in operational_results_agg_df.iterrows():
        operational_results_agg_df.percent_total_power[indx] = \
            operational_results_agg_df.weighted_power_mwh[indx] \
            / lz_period_power_df.weighted_power_mwh[indx[0], indx[1]]*100.0

    # Rename the columns for the final table
    operational_results_agg_df.columns = (["Annual Energy (MWh)",
                                           "% Total Power"])

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> Energy Production <--\n")
        operational_results_agg_df.to_string(outfile)
        outfile.write("\n")


def import_results_into_database(scenario_id, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("dispatch all")
    # dispatch_all.csv
    c.execute(
        """DELETE FROM results_dispatch_all WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_dispatch_all"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_dispatch_all""" + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        load_zone VARCHAR(32),
        technology VARCHAR(32),
        power_mw FLOAT,
        PRIMARY KEY (scenario_id, project, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory, "dispatch_all.csv"), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        reader.next()  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            technology = row[7]
            power_mw = row[8]
            c.execute(
                """INSERT INTO temp_results_dispatch_all"""
                + str(scenario_id) + """
                (scenario_id, project, period, horizon, timepoint,
                horizon_weight, number_of_hours_in_timepoint,
                load_zone, technology, power_mw)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', '{}',
                {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_dispatch_all
        (scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw)
        SELECT
        scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw
        FROM temp_results_dispatch_all""" + str(scenario_id) + """
        ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_dispatch_all""" + str(scenario_id) +
        """;"""
    )
    db.commit()
