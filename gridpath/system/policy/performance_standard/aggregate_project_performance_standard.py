# Copyright 2022 (c) Crown Copyright, GC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Aggregate carbon emissions and energy from the project-timepoint level to
the performance zone - period level.
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

    def total_performance_standard_emissions_rule(mod, z, p):
        """
        Calculate total emissions from all performance standard projects in performance
        standard zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            mod.Project_Carbon_Emissions[g, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (g, tmp) in mod.PERFORMANCE_STANDARD_OPR_TMPS
            if g in mod.PERFORMANCE_STANDARD_PRJS_BY_PERFORMANCE_STANDARD_ZONE[z]
            and tmp in mod.TMPS_IN_PRD[p]
        )

    m.Total_Performance_Standard_Project_Emissions = Expression(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD, rule=total_performance_standard_emissions_rule
    )

    def total_performance_standard_energy_rule(mod, z, p):
        """
        Calculate total emission allowance from all carbon tax projects in carbon
        tax zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            mod.Power_Provision_MW[g, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (g, tmp) in mod.PERFORMANCE_STANDARD_OPR_TMPS
            if g in mod.PERFORMANCE_STANDARD_PRJS_BY_PERFORMANCE_STANDARD_ZONE[z]
            and tmp in mod.TMPS_IN_PRD[p]
        )

    m.Total_Performance_Standard_Project_Energy = Expression(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD, rule=total_performance_standard_energy_rule
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
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "performance_standard_total_project.csv",
        ),
        "w",
        newline="",
    ) as performance_standard_results_file:
        writer = csv.writer(performance_standard_results_file)
        writer.writerow(
            [
                "performance_standard_zone",
                "period",
                "discount_factor",
                "number_years_represented",
                "performance_standard_tco2_per_mwh",
                "project_performance_standard_total_carbon_emissions_tco2",
                "project_performance_standard_total_energy_mwh",
            ]
        )
        for (z, p) in m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD:
            writer.writerow(
                [
                    z,
                    p,
                    m.discount_factor[p],
                    m.number_years_represented[p],
                    float(m.performance_standard[z, p]),
                    value(m.Total_Performance_Standard_Project_Emissions[z, p]),
                    value(m.Total_Performance_Standard_Project_Energy[z, p]),
                ]
            )


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
        print("system performance standard emissions (project)")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_system_performance_standard",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "performance_standard_total_project.csv"), "r"
    ) as emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            performance_standard_zone = row[0]
            period = row[1]
            performance_standard = row[4]
            project_performance_standard_emissions = row[5]
            project_performance_standard_energy = row[6]
            results.append(
                (
                    scenario_id,
                    performance_standard_zone,
                    period,
                    subproblem,
                    stage,
                    performance_standard,
                    project_performance_standard_emissions,
                    project_performance_standard_energy,
                )
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_system_performance_standard{}
         (scenario_id, performance_standard_zone, period, subproblem_id, stage_id,
         performance_standard_tco2_per_mwh, project_performance_standard_total_carbon_emissions_tco2, 
         project_performance_standard_total_energy_mwh)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?);
         """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_performance_standard
        (scenario_id, performance_standard_zone, period, subproblem_id, stage_id,
        performance_standard_tco2_per_mwh, project_performance_standard_total_carbon_emissions_tco2, 
        project_performance_standard_total_energy_mwh)
        SELECT
        scenario_id, performance_standard_zone, period, subproblem_id, stage_id,
        performance_standard_tco2_per_mwh, project_performance_standard_total_carbon_emissions_tco2, 
        project_performance_standard_total_energy_mwh
        FROM temp_results_system_performance_standard{}
         ORDER BY scenario_id, performance_standard_zone, period, subproblem_id, 
        stage_id;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)
