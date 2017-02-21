#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simplest implementation with a MWh target
"""

import csv
import os.path
import pandas as pd

from pyomo.environ import Set, Param, Expression, NonNegativeReals, \
    Constraint, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.RPS_ZONES = Set()
    m.RPS_ZONE_PERIODS_WITH_RPS = \
        Set(dimen=2, within=m.RPS_ZONES * m.PERIODS)
    m.rps_target_mwh = Param(m.RPS_ZONE_PERIODS_WITH_RPS,
                             within=NonNegativeReals)

    m.RPS_PROJECTS = Set(within=m.PROJECTS)
    m.rps_zone = Param(m.RPS_PROJECTS, within=m.RPS_ZONES)

    def determine_rps_generators_by_rps_zone(mod, rps_z):
        return [p for p in mod.RPS_PROJECTS if mod.rps_zone[p] == rps_z]

    m.RPS_PROJECTS_BY_RPS_ZONE = \
        Set(m.RPS_ZONES, within=m.RPS_PROJECTS,
            initialize=determine_rps_generators_by_rps_zone)

    def rps_energy_provision_rule(mod, z, p):
        """
        Calculate the delivered RPS energy for each zone and period
        Scheduled power provision (available energy minus reserves minus
        scheduled curtailment) + subhourly delivered energy (from
        providing upward reserves) - subhourly curtailment (from providing
        downward reserves)
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return \
            sum((mod.Power_Provision_MW[g, tmp]
                 + mod.Subhourly_Energy_Delivered_MW[g,tmp]
                 - mod.Subhourly_Curtailment_MW[g, tmp])
                * mod.number_of_hours_in_timepoint[tmp]
                * mod.horizon_weight[mod.horizon[tmp]]
                for g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
                for tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                )

    m.Total_Delivered_RPS_Energy_MWh = \
        Expression(m.RPS_ZONE_PERIODS_WITH_RPS,
                   rule=rps_energy_provision_rule)

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

    def total_curtailed_rps_energy_rule(mod, z, p):
        """
        Calculate how much RPS-eligible energy was curtailed in each RPS zone
        in each period
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum((mod.Scheduled_Curtailment_MW[g, tmp] +
                    mod.Subhourly_Curtailment_MW[g, tmp] -
                    mod.Subhourly_Energy_Delivered_MW[g, tmp])
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   for g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
                   for tmp in mod.TIMEPOINTS_IN_PERIOD[p])
    # TODO: is this only needed for export and, if so, should it be created on
    # export?
    m.Total_Curtailed_RPS_Energy_MWh = \
        Expression(m.RPS_ZONE_PERIODS_WITH_RPS,
                   rule=total_curtailed_rps_energy_rule)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):

    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "rps_zones.tab"),
                     set=m.RPS_ZONES
                     )

    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "rps_targets.tab"),
                     index=m.RPS_ZONE_PERIODS_WITH_RPS,
                     param=m.rps_target_mwh,
                     select=("rps_zone", "period", "rps_target_mwh")
                     )

    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "rps_zone"),
                     param=(m.rps_zone,)
                     )

    data_portal.data()['RPS_PROJECTS'] = {
        None: data_portal.data()['rps_zone'].keys()
    }


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
                           "rps.csv"), "wb") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["rps_zone", "period", "rps_target_mwh",
                         "delivered_rps_energy_mwh",
                         "curtailed_rps_energy_mwh"])
        for (z, p) in m.RPS_ZONE_PERIODS_WITH_RPS:
            writer.writerow([
                z,
                p,
                float(m.rps_target_mwh[z, p]),
                value(m.Total_Delivered_RPS_Energy_MWh[z, p]),
                value(m.Total_Curtailed_RPS_Energy_MWh[z, p])
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

    # Get the input metadata for periods
    periods_df = \
        pd.read_csv(os.path.join(problem_directory, "inputs", "periods.tab"),
                    sep="\t")

    # Join the above
    results_df = pd.DataFrame(
        pd.merge(
            left=pd.merge(left=rps_df,
                          right=rps_duals_df,
                          how="left",
                          left_on=["rps_zone", "period"],
                          right_on=["rps_zone", "period"]
                          ),
            right=periods_df,
            how="left",
            left_on="period",
            right_on="PERIODS"
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
            results_df.dual[indx] / \
            (results_df.discount_factor[indx] *
             results_df.number_years_represented[indx])

    # Set float format options
    pd.options.display.float_format = "{:,.0f}".format

    # Drop unnecessary columns before exporting
    results_df.drop("PERIODS", axis=1, inplace=True)
    results_df.drop("discount_factor", axis=1, inplace=True)
    results_df.drop("number_years_represented", axis=1, inplace=True)

    # Rearrange the columns
    cols = results_df.columns.tolist()
    cols = cols[0:3] + [cols[4]] + [cols[3]] + [cols[5]]
    results_df = results_df[cols]
    results_df.sort_index(inplace=True)
    with open(summary_results_file, "a") as outfile:
        results_df.to_string(outfile)
        outfile.write("\n")
