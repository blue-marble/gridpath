# Copyright 2016-2020 Blue Marble Analytics LLC.
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
Carbon emissions from each carbonaceous project.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Project_Carbon_Emissions`                                      |
    | | *Defined over*: :code:`FUEL_PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | The project's carbon emissions for each timepoint in which the project  |
    | could be operational. Note that this is an emissions *RATE* (per hour)  |
    | and should be multiplied by the timepoint duration and timepoint        |
    | weight to get the total emissions amount during that timepoint.         |
    +-------------------------------------------------------------------------+

    """
    # Expressions
    ###########################################################################

    def carbon_emissions_rule(mod, prj, tmp):
        """
        Emissions from each project based on operational type
        (and whether a project burns fuel). Multiply by the timepoint duration
        and timepoint weight to get the total emissions amount.
        """

        return (
            mod.Total_Fuel_Burn_MMBtu[prj, tmp]
            * mod.co2_intensity_tons_per_mmbtu[mod.fuel[prj]]
        )

    m.Project_Carbon_Emissions = Expression(
        m.FUEL_PRJ_OPR_TMPS, rule=carbon_emissions_rule
    )


# Input-Output
###############################################################################


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
            "carbon_emissions_by_project.csv",
        ),
        "w",
        newline="",
    ) as carbon_emissions_results_file:
        writer = csv.writer(carbon_emissions_results_file)
        writer.writerow(
            [
                "project",
                "period",
                "horizon",
                "timepoint",
                "timepoint_weight",
                "number_of_hours_in_timepoint",
                "load_zone",
                "technology",
                "carbon_emissions_tons",
            ]
        )
        for (p, tmp) in m.FUEL_PRJ_OPR_TMPS:
            writer.writerow(
                [
                    p,
                    m.period[tmp],
                    m.horizon[tmp, m.balancing_type_project[p]],
                    tmp,
                    m.tmp_weight[tmp],
                    m.hrs_in_tmp[tmp],
                    m.load_zone[p],
                    m.technology[p],
                    value(m.Project_Carbon_Emissions[p, tmp]),
                ]
            )


# Database
###############################################################################


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
    # Carbon emission imports by project and timepoint
    if not quiet:
        print("project carbon emissions")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_project_carbon_emissions",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "carbon_emissions_by_project.csv"), "r"
    ) as emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            timepoint_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            technology = row[7]
            carbon_emissions_tons = row[8]

            results.append(
                (
                    scenario_id,
                    project,
                    period,
                    subproblem,
                    stage,
                    horizon,
                    timepoint,
                    timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone,
                    technology,
                    carbon_emissions_tons,
                )
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_carbon_emissions{}
         (scenario_id, project, period, subproblem_id, stage_id,
         horizon, timepoint, timepoint_weight,
         number_of_hours_in_timepoint,
         load_zone, technology, carbon_emission_tons)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_carbon_emissions
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, carbon_emission_tons)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, carbon_emission_tons
        FROM temp_results_project_carbon_emissions{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """
    Aggregate emissions by technology, period, and spinup_or_lookahead
    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("aggregate emissions by technology-period")

    # Delete old emissions by technology
    del_sql = """
        DELETE FROM results_project_carbon_emissions_by_technology_period 
        WHERE scenario_id = ?
        """
    spin_on_database_lock(
        conn=db, cursor=c, sql=del_sql, data=(scenario_id,), many=False
    )

    # Aggregate emissions by technology, period, and spinup_or_lookahead
    agg_sql = """
        INSERT INTO results_project_carbon_emissions_by_technology_period
        (scenario_id, subproblem_id, stage_id, period, load_zone, technology, 
        spinup_or_lookahead, carbon_emission_tons)
        SELECT
        scenario_id, subproblem_id, stage_id, period, load_zone, technology, 
        spinup_or_lookahead, SUM(carbon_emission_tons * timepoint_weight
        * number_of_hours_in_timepoint ) AS carbon_emission_tons 
        FROM results_project_carbon_emissions
        WHERE scenario_id = ?
        GROUP BY subproblem_id, stage_id, period, load_zone, technology, 
        spinup_or_lookahead
        ORDER BY subproblem_id, stage_id, period, load_zone, technology, 
        spinup_or_lookahead;"""
    spin_on_database_lock(
        conn=db, cursor=c, sql=agg_sql, data=(scenario_id,), many=False
    )
