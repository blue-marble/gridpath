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
Contributions to ELCC surface
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, NonNegativeReals, Binary, Expression, \
    value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import subset_init_by_param_value
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.project.operations.operational_types.common_functions import \
    get_param_dict


def add_model_components(m, d, subproblem_stage_directory):
    """

    :param m:
    :param d:
    :return:
    """
    # Which projects contribute to the ELCC surface
    m.contributes_to_elcc_surface = Param(m.PRM_PROJECTS, within=Binary)

    m.ELCC_SURFACE_PROJECTS = Set(
        within=m.PRM_PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PRM_PROJECTS", "contributes_to_elcc_surface", 1
        )
    )

    m.elcc_surface_cap_factor = Param(
        m.ELCC_SURFACE_PROJECTS,
        within=NonNegativeReals
    )

    m.ELCC_SURFACE_PROJECTS_BY_PRM_ZONE = \
        Set(m.PRM_ZONES, within=m.ELCC_SURFACE_PROJECTS,
            initialize=lambda mod, prm_z: subset_init_by_param_value(
                mod, "ELCC_SURFACE_PROJECTS", "prm_zone", prm_z
                )
            )

    # Define the ELCC surface
    # Surface is limited to 1000 facets
    m.PROJECT_PERIOD_ELCC_SURFACE_FACETS = Set(
        dimen=3,
        within=m.ELCC_SURFACE_PROJECTS * m.PERIODS * list(range(1, 1001))
    )

    # The project coefficient for the surface
    # This goes into the piecewise linear constraint for the aggregate ELCC
    # calculation; unless we have a very detailed surface, this coefficient
    # would actually likely only vary by technology (e.g. wind and solar for a
    # 2-dimensional surface), but we have it by project here for maximum
    # flexibility
    m.elcc_surface_coefficient = Param(
        m.PROJECT_PERIOD_ELCC_SURFACE_FACETS, within=NonNegativeReals
    )

    m.PRM_ZONE_PERIODS_FOR_ELCC_SURFACE = Set(
        within=m.PRM_ZONES * m.PERIODS
    )

    # Loads for normalization
    m.prm_peak_load_mw = Param(
        m.PRM_ZONE_PERIODS_FOR_ELCC_SURFACE, within=NonNegativeReals
    )
    m.prm_annual_load_mwh = Param(
        m.PRM_ZONE_PERIODS_FOR_ELCC_SURFACE, within=NonNegativeReals
    )

    # ELCC surface contribution of each project
    def elcc_surface_contribution_rule(mod, prj, p, f):
        """
        
        :param mod: 
        :param prj: 
        :param p: 
        :param f: 
        :return: 
        """
        if (prj, p) in mod.PRJ_OPR_PRDS:
            return mod.elcc_surface_coefficient[prj, p, f] \
                   * mod.prm_peak_load_mw[mod.prm_zone[prj], p] \
                   * mod.ELCC_Eligible_Capacity_MW[prj, p]\
                   * 8760 \
                   * mod.elcc_surface_cap_factor[prj] \
                   / mod.prm_annual_load_mwh[mod.prm_zone[prj], p]
        else:
            return 0

    m.ELCC_Surface_Contribution_MW = Expression(
        m.PROJECT_PERIOD_ELCC_SURFACE_FACETS,
        rule=elcc_surface_contribution_rule
    )


def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage,
    subproblem_stage_directory
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
    # Projects that contribute to the ELCC surface
    data_portal.load(
        filename=os.path.join(
            subproblem_stage_directory, "inputs", "projects.tab"),
        select=("project", "contributes_to_elcc_surface"),
        param=(m.contributes_to_elcc_surface,)
    )

    elcc_df = pd.read_csv(
        os.path.join(subproblem_stage_directory, "inputs",
                     "projects.tab"),
        sep="\t",
        usecols=["project", "contributes_to_elcc_surface",
                 "elcc_surface_cap_factor"],
        dtype=object  # we'll be checking for objects later
    )

    elcc_proj_df = elcc_df[elcc_df["contributes_to_elcc_surface"] == "1"]

    data_portal.data()["elcc_surface_cap_factor"] = get_param_dict(
        df=elcc_proj_df, column_name="elcc_surface_cap_factor",
        cast_as_type=float
    )

    # Project-period-facet
    data_portal.load(
        filename=os.path.join(
            subproblem_stage_directory, "inputs",
            "project_elcc_surface_coefficients.tab"),
        index=m.PROJECT_PERIOD_ELCC_SURFACE_FACETS,
        param=m.elcc_surface_coefficient,
        select=("project", "period", "facet", "elcc_surface_coefficient")
    )

    # Loads for the normalization
    data_portal.load(
        filename=os.path.join(
            subproblem_stage_directory, "inputs",
            "elcc_surface_normalization_loads.tab"
        ),
        index=m.PRM_ZONE_PERIODS_FOR_ELCC_SURFACE,
        param=(m.prm_peak_load_mw, m.prm_annual_load_mwh)
    )


def export_results(scenario_directory, subproblem, stage, m, d, subproblem_stage_directory):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "prm_project_elcc_surface_contribution.csv"),
              "w", newline="") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period", "prm_zone", "facet",
                         "load_zone", "technology", "capacity_mw",
                         "elcc_eligible_capacity_mw",
                         "elcc_surface_coefficient",
                         "elcc_mw"])
        for (prj, period, facet) in m.PROJECT_PERIOD_ELCC_SURFACE_FACETS:
            writer.writerow([
                prj,
                period,
                m.prm_zone[prj],
                facet,
                m.load_zone[prj],
                m.technology[prj],
                value(m.Capacity_MW[prj, period]),
                value(m.ELCC_Eligible_Capacity_MW[prj, period]),
                value(m.elcc_surface_coefficient[prj, period, facet]),
                value(m.ELCC_Surface_Contribution_MW[prj, period, facet])
            ])


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage

    c1 = conn.cursor()

    # Which projects will contribute to the surface and their cap factors
    project_contr_cf = c1.execute("""
        SELECT project, contributes_to_elcc_surface, elcc_surface_cap_factor
        FROM 
        -- Only select project in the scenario's portfolio
        (SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}) as prj_tbl
        LEFT OUTER JOIN 
        -- Only select projects contributing to the PRM
        (SELECT project
        FROM inputs_project_prm_zones
        WHERE project_prm_zone_scenario_id = {}) as prj_prm_tbl
        USING (project)
        -- Get the ELCC surface contribution flag
        LEFT OUTER JOIN 
        (SELECT project, contributes_to_elcc_surface
        FROM inputs_project_elcc_chars
        WHERE project_elcc_chars_scenario_id = {}) as contr_tbl
        USING (project)
        LEFT OUTER JOIN
        -- Get the cap factors for the surface 
        (SELECT project, elcc_surface_cap_factor
        FROM inputs_project_elcc_surface_cap_factors
        WHERE elcc_surface_scenario_id = {}) as cf_tbl
        USING (project)
        ;""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
            subscenarios.ELCC_SURFACE_SCENARIO_ID
        )
    )

    c2 = conn.cursor()
    # The coefficients for the surface
    coefficients = c2.execute("""
        SELECT project, period, facet, elcc_surface_coefficient
        FROM
        (SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}) as prj_tbl
        LEFT OUTER JOIN 
        inputs_project_elcc_surface
        USING (project)
        INNER JOIN inputs_temporal_periods
        USING (period)
        WHERE elcc_surface_scenario_id = {}
        AND temporal_scenario_id = {};""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.ELCC_SURFACE_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    c3 = conn.cursor()
    # The peak and annual load for the normalization
    elcc_norm_loads = c3.execute("""
        SELECT prm_zone, period, prm_peak_load_mw, prm_annual_load_mwh
        FROM 
        -- only select the PRM zones and periods in the scenario and cross 
        -- join them
        (SELECT prm_zone
        FROM inputs_geography_prm_zones
        WHERE prm_zone_scenario_id = {}) as prm_zone_tbl
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as period_tbl
        -- Join to the normalization params
        LEFT OUTER JOIN
        inputs_system_prm_zone_elcc_surface_prm_load
        USING (prm_zone, period)
        WHERE elcc_surface_scenario_id = {}
        """.format(
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.ELCC_SURFACE_SCENARIO_ID
        )
    )

    return project_contr_cf, coefficients, elcc_norm_loads


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
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


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage, conn, subproblem_stage_directory):
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
    project_contr_cf, coefficients, elcc_norm_loads = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_contr_cf_dict = dict()
    for (prj, contr, cf) in project_contr_cf:
        prj_contr_cf_dict[str(prj)] = (contr, cf)

    with open(os.path.join(subproblem_stage_directory, "inputs", "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("contributes_to_elcc_surface")
        header.append("elcc_surface_cap_factor")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            prj = row[0]
            # If project specified add the values
            if prj in list(prj_contr_cf_dict.keys()):
                row.append(prj_contr_cf_dict[prj][0] if prj_contr_cf_dict[
                    prj][0] is not None else ".")
                row.append(prj_contr_cf_dict[prj][1] if prj_contr_cf_dict[
                    prj][1] is not None else ".")
                new_rows.append(row)
            # If project not specified, specify no chars
            else:
                row.append(".")
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(subproblem_stage_directory, "inputs", "projects.tab"), "w", newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)

    with open(os.path.join(subproblem_stage_directory, "inputs",
                           "project_elcc_surface_coefficients.tab"), "w", newline="") as \
            coefficients_file:
        writer = csv.writer(coefficients_file, delimiter="\t", lineterminator="\n")

        # Writer header
        writer.writerow(
            ["project", "period", "facet", "elcc_surface_coefficient"]
        )
        # Write data
        for row in coefficients:
            writer.writerow(row)

    with open(os.path.join(subproblem_stage_directory, "inputs",
                           "elcc_surface_normalization_loads.tab"), "w",
              newline="") as \
            coefficients_file:
        writer = csv.writer(coefficients_file, delimiter="\t",
                            lineterminator="\n")

        # Writer header
        writer.writerow(
            ["prm_zone", "period", "prm_peak_load_mw", "prm_annual_load_mwh"]
        )
        # Write data
        for row in elcc_norm_loads:
            writer.writerow(row)


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
    if not quiet:
        print("project elcc surface")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_elcc_surface",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "prm_project_elcc_surface_contribution.csv"), "r") \
            as elcc_file:
        reader = csv.reader(elcc_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            prm_zone = row[2]
            facet = row[3]
            load_zone = row[4]
            technology = row[5]
            capacity = row[6]
            elcc_eligible_capacity = row[7]
            coefficient = row[8]
            elcc = row[9]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                 prm_zone, facet, technology, load_zone,
                 capacity, elcc_eligible_capacity, coefficient, elcc)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_elcc_surface{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        prm_zone, facet, technology, load_zone,
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_surface_coefficient, elcc_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,  ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_elcc_surface
        (scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, facet, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw, 
        elcc_surface_coefficient, elcc_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, facet, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_surface_coefficient, elcc_mw
        FROM temp_results_project_elcc_surface{}
        ORDER BY scenario_id, project, period, subproblem_id, stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
