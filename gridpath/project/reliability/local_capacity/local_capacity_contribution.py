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
Simple local capacity contribution where each local project contributes a 
fraction of its installed capacity.
"""


import csv
import os.path
from pyomo.environ import Param, PercentFraction, Expression, value

from gridpath.auxiliary.db_interface import import_csv, directories_to_db_values


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
    # The fraction of capacity that counts for the local capacity requirement
    m.local_capacity_fraction = Param(m.LOCAL_CAPACITY_PROJECTS, within=PercentFraction)

    def local_capacity_rule(mod, g, p):
        """

        :param mod:
        :param g:
        :param p:
        :return:
        """
        return mod.Capacity_MW[g, p] * mod.local_capacity_fraction[g]

    m.Local_Capacity_Contribution_MW = Expression(
        m.LOCAL_CAPACITY_PRJ_OPR_PRDS, rule=local_capacity_rule
    )


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
        filename=os.path.join(scenario_directory, "inputs", "projects.tab"),
        select=("project", "local_capacity_fraction"),
        param=(m.local_capacity_fraction,),
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
            "project_local_capacity.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(
            [
                "project",
                "period",
                "local_capacity_zone",
                "technology",
                "load_zone",
                "capacity_mw",
                "local_capacity_fraction",
                "local_capacity_contribution_mw",
            ]
        )
        for prj, period in sorted(m.LOCAL_CAPACITY_PRJ_OPR_PRDS):
            writer.writerow(
                [
                    prj,
                    period,
                    m.local_capacity_zone[prj],
                    m.technology[prj],
                    m.load_zone[prj],
                    value(m.Capacity_MW[prj, period]),
                    value(m.local_capacity_fraction[prj]),
                    value(m.Local_Capacity_Contribution_MW[prj, period]),
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
    project_frac = c.execute(
        """SELECT project, local_capacity_fraction
        FROM 
        (SELECT project
        FROM inputs_project_local_capacity_zones
        WHERE project_local_capacity_zone_scenario_id = {}) as proj_tbl
        LEFT OUTER JOIN 
        (SELECT project, local_capacity_fraction
        FROM inputs_project_local_capacity_chars
        WHERE project_local_capacity_chars_scenario_id = {}) as frac_tbl
        USING (project);""".format(
            subscenarios.PROJECT_LOCAL_CAPACITY_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_LOCAL_CAPACITY_CHARS_SCENARIO_ID,
        )
    )

    return project_frac


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

    # project_frac = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn

    # do stuff here to validate inputs


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

    project_frac = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    prj_frac_dict = {p: "." if f is None else f for (p, f) in project_frac}

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        "r",
    ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("local_capacity_fraction")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_frac_dict.keys()):
                row.append(prj_frac_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        "w",
        newline="",
    ) as projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)


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
        which_results="project_local_capacity",
    )
