# Copyright 2016-2024 Blue Marble Analytics LLC.
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
Get contributions for each project and policy
"""

import csv
import os.path
from pyomo.environ import Param, Set, Expression, value, Reals

from gridpath.auxiliary.auxiliary import (
    get_required_subtype_modules,
    cursor_to_df,
    subset_init_by_set_membership,
)
from gridpath.auxiliary.db_interface import (
    update_prj_zone_column,
    determine_table_subset_by_start_and_column,
    directories_to_db_values,
    import_csv,
)
from gridpath.common_functions import create_results_df
from gridpath.project.operations.common_functions import load_operational_type_modules
from gridpath.auxiliary.validations import write_validation_to_database, validate_idxs
import gridpath.project.policy.compliance_types as compliance_type_init
from gridpath.project import PROJECT_TIMEPOINT_DF


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
    """ """

    # Dynamic Inputs
    ###########################################################################

    # required_operational_modules = get_required_subtype_modules(
    #     scenario_directory=scenario_directory,
    #     weather_iteration=weather_iteration,
    #     hydro_iteration=hydro_iteration,
    #     availability_iteration=availability_iteration,
    #     subproblem=subproblem,
    #     stage=stage,
    #     which_type="operational_type",
    # )
    #
    # imported_compliance_modules = load_operational_type_modules(
    #     required_operational_modules
    # )

    m.PROJECT_POLICY_ZONES = Set(dimen=3, within=m.PROJECTS * m.POLICIES_ZONES)
    m.compliance_type = Param(
        m.PROJECT_POLICY_ZONES,
        within=[
            "f_output",
            "f_capacity",
            "flat_horizon",
        ],
    )

    m.f_slope = Param(m.PROJECT_POLICY_ZONES, within=Reals, default=0)
    m.f_intercept = Param(m.PROJECT_POLICY_ZONES, within=Reals, default=0)

    def prj_policy_zone_opr_tmps_init(mod):
        opr_tmps = list()
        for prj, policy, zone in mod.PROJECT_POLICY_ZONES:
            for _prj, tmp in mod.PRJ_OPR_TMPS:
                if prj == _prj:
                    opr_tmps.append((prj, policy, zone, tmp))

        return opr_tmps

    m.PRJ_POLICY_ZONE_OPR_TMPS = Set(dimen=4, initialize=prj_policy_zone_opr_tmps_init)

    # Expressions
    ###########################################################################

    def contribution_in_timepoint(mod, prj, policy, zone, tmp):
        """ """
        # compliance_type = mod.compliance_type[prj]
        # if hasattr(imported_compliance_modules[compliance_type], "contribution_in_timepoint"):
        #     return imported_compliance_modules[compliance_type].contribution_in_timepoint(
        #         mod, prj, policy, tmp
        #     )
        # else:
        #     return compliance_type_init.contribution_in_timepoint(mod, prj, policy, tmp)

        return (
            mod.f_slope[prj, policy, zone] * mod.Power_Provision_MW[prj, tmp]
            + mod.f_intercept[prj, policy, zone]
        )

    m.Policy_Contribution_in_Timepoint = Expression(
        m.PRJ_POLICY_ZONE_OPR_TMPS, rule=contribution_in_timepoint
    )

    # def contribution_in_horizon(mod, prj, policy, bt, h):
    #     """
    #     """
    #     op_type = mod.operational_type[prj]
    #     if hasattr(imported_compliance_modules[op_type], "contribution_in_horizon"):
    #         return imported_compliance_modules[op_type].contribution_in_horizon(
    #             mod, prj, policy, bt, h
    #         )
    #     else:
    #         return compliance_type_init.contribution_in_horizon(mod, prj, policy, bt, h)
    #
    # m.Policy_Contribution_in_Horizon = Expression(
    #     m.PRJ_POLICY_ZONE_OPR_TMPSS, rule=contribution_in_timepoint
    # )


# Input-Output
###############################################################################


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
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "project_policy_zones.tab",
        ),
        index=m.PROJECT_POLICY_ZONES,
        param=(m.compliance_type, m.f_slope, m.f_intercept),
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

    results_columns = [
        "period",
        "policy_contribution",
    ]
    data = [
        [
            prj,
            p,
            z,
            tmp,
            m.period[tmp],
            value(m.Policy_Contribution_in_Timepoint[prj, p, z, tmp]),
        ]
        for (prj, p, z, tmp) in m.PRJ_POLICY_ZONE_OPR_TMPS
    ]

    results_df = create_results_df(
        index_columns=["project", "policy_name", "policy_zone", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    results_df.to_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_policy_zone_timepoint.csv",
        ),
        sep=",",
        index=True,
    )


# Database
###############################################################################


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

    # Get the energy-target zones for project in our portfolio and with zones in our
    # Energy target zone
    project_policy_zones = c.execute(
        f"""SELECT project, policy_name, policy_zone, compliance_type, 
        f_slope, f_intercept
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        ) as prj_tbl
        LEFT OUTER JOIN 
        -- Get energy_target zones for those projects
        (SELECT project, policy_name, policy_zone, compliance_type, 
        f_slope, f_intercept
            FROM inputs_project_policy_zones
            WHERE project_policy_zone_scenario_id = {subscenarios.PROJECT_POLICY_ZONE_SCENARIO_ID}
        ) as prj_energy_target_zone_tbl
        USING (project)
        -- Filter out projects whose RPS zone is not one included in our 
        -- energy_target_zone_scenario_id
        WHERE (policy_name, policy_zone) in (
                SELECT policy_name, policy_zone
                    FROM inputs_geography_policy_zones
                    WHERE policy_zone_scenario_id = {subscenarios.POLICY_ZONE_SCENARIO_ID}
        );
        """
    )

    return project_policy_zones


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
    project_policy_zones = get_inputs_from_database(
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
            "project_policy_zones.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "project",
                "policy_name",
                "policy_zone",
                "compliance_type",
                "f_slope",
                "f_intercept",
            ]
        )

        for row in project_policy_zones:
            # It's OK if targets are not specified; they default to 0
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


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
        which_results="project_policy_zone_timepoint",
    )
