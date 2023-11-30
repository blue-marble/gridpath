# Copyright 2016-2023 Blue Marble Analytics LLC.
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
Simplest PRM contribution where each PRM project contributes a fraction of 
its installed capacity. Note that projects contributing through the ELCC surface can
also simultaneous contribute a simple fraction of their capacity (the fraction
defaults to 0 if not specified).
"""


import csv
import os.path
from pyomo.environ import Param, PercentFraction, Expression, value

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.db_interface import import_csv, directories_to_db_values
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_values,
    validate_missing_inputs,
)


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :return:
    """
    # The fraction of ELCC-eligible capacity that counts for the PRM via the
    # simple PRM method (whether or not project also contributes through the
    # ELCC surface)
    m.elcc_simple_fraction = Param(
        m.PRM_PROJECTS, m.PERIODS, within=PercentFraction, default=0
    )

    def elcc_simple_rule(mod, g, p):
        """

        :param g:
        :param p:
        :return:
        """
        return mod.ELCC_Eligible_Capacity_MW[g, p] * mod.elcc_simple_fraction[g, p]

    m.PRM_Simple_Contribution_MW = Expression(m.PRM_PRJ_OPR_PRDS, rule=elcc_simple_rule)


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
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
        filename=os.path.join(
            scenario_directory,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "prm_projects_simple_elcc.tab",
        ),
        param=m.elcc_simple_fraction,
    )


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
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
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_elcc_simple.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(
            [
                "project",
                "period",
                "prm_zone",
                "technology",
                "load_zone",
                "capacity_mw",
                "elcc_eligible_capacity_mw",
                "elcc_simple_fraction",
                "elcc_mw",
            ]
        )
        for prj, period in sorted(m.PRM_PRJ_OPR_PRDS):
            writer.writerow(
                [
                    prj,
                    period,
                    m.prm_zone[prj],
                    m.technology[prj],
                    m.load_zone[prj],
                    value(m.Capacity_MW[prj, period]),
                    value(m.ELCC_Eligible_Capacity_MW[prj, period]),
                    value(m.elcc_simple_fraction[prj, period]),
                    value(m.PRM_Simple_Contribution_MW[prj, period]),
                ]
            )


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    project_fractions = c.execute(
        """SELECT project, period, elcc_simple_fraction
        FROM (
            SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {portfolio}
         ) as portfolio
         LEFT OUTER JOIN (
            SELECT project
            FROM inputs_project_prm_zones
            WHERE project_prm_zone_scenario_id = {prm_zone}
        ) as proj_tbl
        USING (project)
        LEFT OUTER JOIN (
            SELECT project, project_elcc_simple_scenario_id
            FROM inputs_project_elcc_chars
            WHERE project_elcc_chars_scenario_id = {prj_elcc} 
        )
        USING (project)
        LEFT OUTER JOIN (
            SELECT project, project_elcc_simple_scenario_id, period, 
            elcc_simple_fraction
            FROM inputs_project_elcc_simple
        ) as frac_tbl
        USING (project, project_elcc_simple_scenario_id)
        WHERE period in (
            SELECT period FROM inputs_temporal
            WHERE temporal_scenario_id = {temporal}
        )
        ;""".format(
            portfolio=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            prm_zone=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            prj_elcc=subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
        )
    )

    return project_fractions


def validate_inputs(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    project_fractions = get_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    df = cursor_to_df(project_fractions)

    # Make sure fraction is specified
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_elcc_chars",
        severity="High",
        errors=validate_values(df, ["elcc_simple_fraction"], min=0, max=1),
    )

    # Make sure fraction is specified
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_elcc_chars",
        severity="High",
        errors=validate_missing_inputs(df, "elcc_simple_fraction"),
    )


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and write out the model input
    projects.tab file (to be precise, amend it).
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    project_fractions = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "prm_projects_simple_elcc.tab",
        ),
        "w",
        newline="",
    ) as projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerow(["project", "period", "elcc_simple_fraction"])
        for row in project_fractions:
            writer.writerow(row)


def import_results_into_database(
    scenario_id,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    c,
    db,
    results_directory,
    quiet,
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    import_csv(
        conn=db,
        cursor=c,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        quiet=quiet,
        results_directory=results_directory,
        which_results="project_elcc_simple",
    )
