"""
Aggregate carbon emissions from the project-timepoint level to
the carbon tax zone - period level.
"""
from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    def total_carbon_emissions_rule(mod, z, p):
        """
        Calculate total emissions from all carbonaceous projects in carbon
        tax zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.Project_Carbon_Emissions[g, tmp]
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   for (g, tmp) in mod.CARBON_TAX_PRJ_OPR_TMPS
                   if g in mod.CARBON_TAX_PRJS_BY_CARBON_TAX_ZONE[z]
                   and tmp in mod.TMPS_IN_PRD[p]
                   )

    m.Total_Carbon_Tax_Project_Emissions = Expression(
        m.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX,
        rule=total_carbon_emissions_rule
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
                           "results", "carbon_tax_total_project.csv"),
              "w", newline="") as carbon_results_file:
        writer = csv.writer(carbon_results_file)
        writer.writerow(["carbon_tax_zone", "period",
                         "discount_factor", "number_years_represented",
                         "carbon_tax",
                         "project_carbon_emissions"])
        for (z, p) in m.CARBON_TAX_ZONE_PERIODS_WITH_CARBON_TAX:
            writer.writerow([
                z,
                p,
                m.discount_factor[p],
                m.number_years_represented[p],
                float(m.carbon_tax[z, p]),
                value(m.Total_Carbon_Tax_Project_Emissions[z, p])
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
        print("system carbon tax emissions (project)")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_system_carbon_tax_emissions",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "carbon_tax_total_project.csv"), "r") as \
            emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            carbon_tax_zone = row[0]
            period = row[1]
            carbon_tax = row[4]
            project_carbon_emissions = row[5]

            results.append(
                (scenario_id, carbon_tax_zone, period, subproblem, stage,
                 carbon_tax, project_carbon_emissions)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_system_carbon_tax_emissions{}
         (scenario_id, carbon_tax_zone, period, subproblem_id, stage_id,
         carbon_tax, total_emissions)
         VALUES (?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_carbon_tax_emissions
        (scenario_id, carbon_tax_zone, period, subproblem_id, stage_id,
        carbon_tax, total_emissions)
        SELECT
        scenario_id, carbon_tax_zone, period, subproblem_id, stage_id,
        carbon_tax, total_emissions
        FROM temp_results_system_carbon_tax_emissions{}
         ORDER BY scenario_id, carbon_tax_zone, period, subproblem_id, 
        stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
