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
Contributions to ELCC surface
"""

import csv
import os.path
from pyomo.environ import Param, Set, NonNegativeReals, Binary, Expression, value, Any

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
    m.ELCC_SURFACE_PRM_ZONE_PERIODS = Set(dimen=3, within=Any * m.PRM_ZONES * m.PERIODS)

    # Loads for normalization
    m.prm_peak_load_mw = Param(m.ELCC_SURFACE_PRM_ZONE_PERIODS, within=NonNegativeReals)
    m.prm_annual_load_mwh = Param(
        m.ELCC_SURFACE_PRM_ZONE_PERIODS, within=NonNegativeReals
    )

    # ELCC surface for each PRM project
    m.elcc_surface_name = Param(m.PRM_PROJECTS, within=Any, default=None)
    m.elcc_surface_cap_factor = Param(
        m.PRM_PROJECTS, within=(NonNegativeReals | {None}), default=None
    )

    # Two-dimensional set of the ELCC surface name and the project that contribute to
    # that surface
    m.ELCC_SURFACE_PROJECTS = Set(
        dimen=2,
        initialize=lambda mod: [
            (mod.elcc_surface_name[prj], prj)
            for prj in mod.PRM_PROJECTS
            if mod.elcc_surface_name[prj] is not None
        ],
    )

    m.ELCC_SURFACE_PROJECTS_BY_PRM_ZONE = Set(
        m.PRM_ZONES,
        dimen=2,
        within=m.ELCC_SURFACE_PROJECTS,
        initialize=lambda mod, prm_z: [
            (surface, prj)
            for (surface, prj) in mod.ELCC_SURFACE_PROJECTS
            if mod.prm_zone[prj] == prm_z
        ],
    )

    # Define the ELCC surface
    # Surface is limited to 1000 facets
    m.ELCC_SURFACE_PROJECT_PERIOD_FACETS = Set(
        dimen=4, within=m.ELCC_SURFACE_PROJECTS * m.PERIODS * list(range(1, 1001))
    )

    # The project coefficient for the surface
    # This goes into the piecewise linear constraint for the aggregate ELCC
    # calculation; unless we have a very detailed surface, this coefficient
    # would actually likely only vary by technology (e.g. wind and solar for a
    # 2-dimensional surface), but we have it by project here for maximum
    # flexibility
    m.elcc_surface_coefficient = Param(
        m.ELCC_SURFACE_PROJECT_PERIOD_FACETS, within=NonNegativeReals
    )

    # ELCC surface contribution of each project
    def elcc_surface_contribution_rule(mod, surface, prj, p, f):
        """

        :param mod:
        :param surface:
        :param prj:
        :param p:
        :param f:
        :return:
        """
        if (prj, p) in mod.PRJ_OPR_PRDS:
            return (
                mod.elcc_surface_coefficient[surface, prj, p, f]
                * mod.prm_peak_load_mw[surface, mod.prm_zone[prj], p]
                * mod.ELCC_Eligible_Capacity_MW[prj, p]
                * 8760
                * mod.elcc_surface_cap_factor[prj]
                / mod.prm_annual_load_mwh[surface, mod.prm_zone[prj], p]
            )
        else:
            return 0

    m.ELCC_Surface_Contribution_MW = Expression(
        m.ELCC_SURFACE_PROJECT_PERIOD_FACETS, rule=elcc_surface_contribution_rule
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
    # Loads for the normalization
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "elcc_surface_normalization_loads.tab",
        ),
        index=m.ELCC_SURFACE_PRM_ZONE_PERIODS,
        param=(m.prm_peak_load_mw, m.prm_annual_load_mwh),
    )

    # Projects that contribute to the ELCC surface
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        select=("project", "elcc_surface_name", "elcc_surface_cap_factor"),
        param=(
            m.elcc_surface_name,
            m.elcc_surface_cap_factor,
        ),
    )

    # Surface-project-period-facet
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "project_elcc_surface_coefficients.tab",
        ),
        index=m.ELCC_SURFACE_PROJECT_PERIOD_FACETS,
        param=m.elcc_surface_coefficient,
        select=(
            "elcc_surface_name",
            "project",
            "period",
            "facet",
            "elcc_surface_coefficient",
        ),
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
            "project_elcc_surface.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(
            [
                "elcc_surface_name",
                "project",
                "period",
                "prm_zone",
                "facet",
                "load_zone",
                "technology",
                "capacity_mw",
                "elcc_eligible_capacity_mw",
                "elcc_surface_coefficient",
                "elcc_mw",
            ]
        )
        for surface, prj, period, facet in m.ELCC_SURFACE_PROJECT_PERIOD_FACETS:
            writer.writerow(
                [
                    surface,
                    prj,
                    period,
                    m.prm_zone[prj],
                    facet,
                    m.load_zone[prj],
                    m.technology[prj],
                    value(m.Capacity_MW[prj, period]),
                    value(m.ELCC_Eligible_Capacity_MW[prj, period]),
                    value(m.elcc_surface_coefficient[surface, prj, period, facet]),
                    value(m.ELCC_Surface_Contribution_MW[surface, prj, period, facet]),
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
    c1 = conn.cursor()

    # Which projects will contribute to the surface and their cap factors
    project_contr_cf = c1.execute(
        """
        SELECT project, elcc_surface_name, elcc_surface_cap_factor
        FROM 
        -- Only select project in the scenario's portfolio
        (SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {portfolio}) as prj_tbl
        LEFT OUTER JOIN 
        -- Only select projects contributing to the PRM
        (SELECT project
        FROM inputs_project_prm_zones
        WHERE project_prm_zone_scenario_id = {prj_prm_zone}) as prj_prm_tbl
        USING (project)
        -- Get the ELCC surface contribution flag
        LEFT OUTER JOIN
        -- Get the cap factors for the surface 
        (SELECT project, elcc_surface_name, elcc_surface_cap_factor
        FROM inputs_project_elcc_surface_cap_factors
        WHERE elcc_surface_scenario_id = {elcc_surface}) as cf_tbl
        USING (project)
        ;""".format(
            portfolio=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            prj_prm_zone=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            elcc_surface=subscenarios.ELCC_SURFACE_SCENARIO_ID,
        )
    )

    c2 = conn.cursor()
    # The coefficients for the surface
    coefficients = c2.execute(
        """
        SELECT elcc_surface_name, project, period, facet, elcc_surface_coefficient
        FROM
        (SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {portfolio}) as prj_tbl
        LEFT OUTER JOIN 
        inputs_project_elcc_surface
        USING (project)
        INNER JOIN inputs_temporal_periods
        USING (period)
        WHERE elcc_surface_scenario_id = {elcc_surface}
        AND temporal_scenario_id = {temporal};""".format(
            portfolio=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            elcc_surface=subscenarios.ELCC_SURFACE_SCENARIO_ID,
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
        )
    )

    c3 = conn.cursor()
    # The peak and annual load for the normalization
    elcc_norm_loads = c3.execute(
        """
        SELECT elcc_surface_name, prm_zone, period, prm_peak_load_mw, 
        prm_annual_load_mwh
        FROM 
        -- only select the PRM zones and periods in the scenario and cross 
        -- join them
        (SELECT prm_zone
        FROM inputs_geography_prm_zones
        WHERE prm_zone_scenario_id = {prm_zone}) as prm_zone_tbl
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal}) as period_tbl
        -- Join to the normalization params
        LEFT OUTER JOIN
        inputs_system_prm_zone_elcc_surface_prm_load
        USING (prm_zone, period)
        WHERE elcc_surface_scenario_id = {elcc_surface}
        """.format(
            prm_zone=subscenarios.PRM_ZONE_SCENARIO_ID,
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            elcc_surface=subscenarios.ELCC_SURFACE_SCENARIO_ID,
        )
    )

    return project_contr_cf, coefficients, elcc_norm_loads


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

    # project_contr, coefficients = get_inputs_from_database(
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
    projects.tab (to be precise, amend it) and
    project_elcc_surface_coefficients.tab files.
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

    project_contr_cf, coefficients, elcc_norm_loads = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    # Make a dict for easy access
    prj_contr_cf_dict = dict()
    for prj, contr, cf in project_contr_cf:
        prj_contr_cf_dict[str(prj)] = (contr, cf)

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
        header.append("elcc_surface_name")
        header.append("elcc_surface_cap_factor")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            prj = row[0]
            # If project specified add the values
            if prj in list(prj_contr_cf_dict.keys()):
                row.append(
                    prj_contr_cf_dict[prj][0]
                    if prj_contr_cf_dict[prj][0] is not None
                    else "."
                )
                row.append(
                    prj_contr_cf_dict[prj][1]
                    if prj_contr_cf_dict[prj][1] is not None
                    else "."
                )
                new_rows.append(row)
            # If project not specified, specify no chars
            else:
                row.append(".")
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

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "project_elcc_surface_coefficients.tab",
        ),
        "w",
        newline="",
    ) as coefficients_file:
        writer = csv.writer(coefficients_file, delimiter="\t", lineterminator="\n")

        # Writer header
        writer.writerow(
            [
                "elcc_surface_name",
                "project",
                "period",
                "facet",
                "elcc_surface_coefficient",
            ]
        )
        # Write data
        for row in coefficients:
            writer.writerow(row)

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "elcc_surface_normalization_loads.tab",
        ),
        "w",
        newline="",
    ) as coefficients_file:
        writer = csv.writer(coefficients_file, delimiter="\t", lineterminator="\n")

        # Writer header
        writer.writerow(
            [
                "elcc_surface_name",
                "prm_zone",
                "period",
                "prm_peak_load_mw",
                "prm_annual_load_mwh",
            ]
        )
        # Write data
        for row in elcc_norm_loads:
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
        which_results="project_elcc_surface",
    )
