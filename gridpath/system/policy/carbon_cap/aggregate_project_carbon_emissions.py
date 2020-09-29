#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate carbon emissions from the project-timepoint level to
the carbon cap zone - period level.
"""
from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.dynamic_components import \
    carbon_cap_balance_emission_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    def total_carbon_emissions_rule(mod, z, p):
        """
        Calculate total emissions from all carbonaceous projects in carbon
        cap zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.Project_Carbon_Emissions[g, tmp]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   for (g, tmp) in mod.CRBN_PRJ_OPR_TMPS
                   if g in mod.CRBN_PRJS_BY_CARBON_CAP_ZONE[z]
                   and tmp in mod.TMPS_IN_PRD[p]
                   )

    m.Total_Carbon_Cap_Project_Emissions = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=total_carbon_emissions_rule
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds project emissions to carbon balance
    """

    getattr(dynamic_components, carbon_cap_balance_emission_components).append(
        "Total_Carbon_Cap_Project_Emissions"
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, str(subproblem), str(stage),
                           "results", "carbon_cap_total_project.csv"),
              "w", newline="") as carbon_results_file:
        writer = csv.writer(carbon_results_file)
        writer.writerow(["carbon_cap_zone", "period",
                         "discount_factor", "number_years_represented",
                         "carbon_cap_target",
                         "project_carbon_emissions"])
        for (z, p) in m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP:
            writer.writerow([
                z,
                p,
                m.discount_factor[p],
                m.number_years_represented[p],
                float(m.carbon_cap_target[z, p]),
                value(m.Total_Carbon_Cap_Project_Emissions[z, p])
            ])


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
    # Carbon emissions by in-zone projects
    if not quiet:
        print("system carbon emissions (project)")
    
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_system_carbon_emissions",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "carbon_cap_total_project.csv"), "r") as \
            emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            carbon_cap_zone = row[0]
            period = row[1]
            carbon_cap = row[4]
            project_carbon_emissions = row[5]
            
            results.append(
                (scenario_id, carbon_cap_zone, period, subproblem, stage,
                 carbon_cap, project_carbon_emissions)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_system_carbon_emissions{}
         (scenario_id, carbon_cap_zone, period, subproblem_id, stage_id,
         carbon_cap, in_zone_project_emissions)
         VALUES (?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_carbon_emissions
        (scenario_id, carbon_cap_zone, period, subproblem_id, stage_id,
        carbon_cap, in_zone_project_emissions)
        SELECT
        scenario_id, carbon_cap_zone, period, subproblem_id, stage_id,
        carbon_cap, in_zone_project_emissions
        FROM temp_results_system_carbon_emissions{}
         ORDER BY scenario_id, carbon_cap_zone, period, subproblem_id, 
        stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
