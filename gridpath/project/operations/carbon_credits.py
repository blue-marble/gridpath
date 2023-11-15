# Copyright 2016-2023 Blue Marble Analytics LLC
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

"""

import csv
import os.path
from pyomo.environ import Param, Set, NonNegativeReals, Var, Constraint, value

from gridpath.auxiliary.auxiliary import (
    cursor_to_df,
    subset_init_by_param_value,
    get_required_subtype_modules,
    subset_init_by_set_membership,
)
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.common_functions import create_results_df
from gridpath.project import PROJECT_PERIOD_DF
from gridpath.project.operations.common_functions import load_operational_type_modules
import gridpath.project.operations.operational_types as op_type_init


def add_model_components(
    m, d, scenario_directory, weather_iteration, hydro_iteration, subproblem, stage
):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`CARBON_CREDITS_PRJS`                                               |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | Two set of carbonaceous projects we need to track for the carbon credits.   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`carbon_credits_zone`                                           |
    | | *Defined over*: :code:`CARBON_CREDITS_PRJS`                           |
    | | *Within*: :code:`CARBON_CREDITS_ZONES`                                |
    |                                                                         |
    | This param describes the carbon credits zone for each carbon credits    |
    | project.                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`intensity_threshold_emissions_toCO2_per_MWh`                   |
    | | *Defined over*: :code:`CARBON_CREDITS_PRJ_OPR_PRDS`                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | This param describes the intensity-based emissions threshold for each   |
    | carbon credits project. Additive with the absolute emissions threshold. |
    +-------------------------------------------------------------------------+
    | | :code:`absolute_threshold_emissions_toCO2`                            |
    | | *Defined over*: :code:`CARBON_CREDITS_PRJ_OPR_PRDS`                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | This param describes the absolute emissions threshold for each carbon   |
    | credits project. Additive with the relative emissions threshold.        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`CARBON_CREDITS_PRJS_BY_CARBON_CREDITS_ZONE`                    |
    | | *Defined over*: :code:`CARBON_CREDITS_ZONES`                          |
    | | *Within*: :code:`CARBON_CREDITS_PRJS`                                 |
    |                                                                         |
    | Indexed set that describes the list of carbonaceous projects for each   |
    | carbon credits zone.                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`CARBON_CREDITS_PRJ_OPR_TMPS`                                   |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | Two-dimensional set that defines all project-timepoint combinations     |
    | when a carbon credits project can be operational.                       |
    +-------------------------------------------------------------------------+
    | | :code:`CARBON_CREDITS_PRJ_OPR_PRDS`                                   |
    | | *Within*: :code:`PRJ_OPR_PRDS`                                        |
    |                                                                         |
    | Two-dimensional set that defines all project-period combinations        |
    | when a carbon credits project can be operational.                       |
    +-------------------------------------------------------------------------+

    """
    # Dynamic Inputs
    ###########################################################################

    required_operational_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Sets
    ###########################################################################

    m.CARBON_CREDITS_PRJS = Set(within=m.PROJECTS)

    m.CARBON_CREDITS_PRJ_OPR_TMPS = Set(
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_TMPS",
            index=0,
            membership_set=mod.CARBON_CREDITS_PRJS,
        ),
    )

    m.CARBON_CREDITS_PRJ_OPR_PRDS = Set(
        within=m.PRJ_OPR_PRDS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_PRDS",
            index=0,
            membership_set=mod.CARBON_CREDITS_PRJS,
        ),
    )

    # Input Params
    ###########################################################################

    m.carbon_credits_zone = Param(m.CARBON_CREDITS_PRJS, within=m.CARBON_CREDITS_ZONES)

    m.intensity_threshold_emissions_toCO2_per_MWh = Param(
        m.CARBON_CREDITS_PRJ_OPR_PRDS,
        within=NonNegativeReals,
        default=0,
    )

    m.absolute_threshold_emissions_toCO2 = Param(
        m.CARBON_CREDITS_PRJ_OPR_PRDS,
        within=NonNegativeReals,
        default=0,
        validate=lambda mod, value, prj, prd: value == 0
        if mod.intensity_threshold_emissions_toCO2_per_MWh[prj, prd] > 0
        else value >= 0,  # pick one of intensity-based and absolute thresholds
    )

    # Derived Sets
    ###########################################################################

    m.CARBON_CREDITS_PRJS_BY_CARBON_CREDITS_ZONE = Set(
        m.CARBON_CREDITS_ZONES,
        within=m.CARBON_CREDITS_PRJS,
        initialize=lambda mod, z: subset_init_by_param_value(
            mod, "CARBON_CREDITS_PRJS", "carbon_credits_zone", z
        ),
    )

    # Variables
    ###########################################################################

    m.Project_Carbon_Credits_Generated = Var(
        m.CARBON_CREDITS_PRJ_OPR_PRDS, within=NonNegativeReals
    )

    def generated_credits_rule(mod, prj, prd):
        """
        The credits generated by each project.
        """
        op_type = mod.operational_type[prj]
        total_power_provision_in_prd = sum(
            (
                imported_operational_modules[op_type].power_provision_rule(mod, p, tmp)
                if hasattr(
                    imported_operational_modules[op_type], "power_provision_rule"
                )
                else op_type_init.power_provision_rule(mod, p, tmp)
            )
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (p, tmp) in mod.CARBON_CREDITS_PRJ_OPR_TMPS
            if mod.period[tmp] == prd and p == prj
        )
        return mod.Project_Carbon_Credits_Generated[prj, prd] <= (
            total_power_provision_in_prd
            * mod.intensity_threshold_emissions_toCO2_per_MWh[prj, prd]
            + mod.absolute_threshold_emissions_toCO2[prj, prd]
            - sum(
                mod.Project_Carbon_Emissions[p, tmp]
                * mod.hrs_in_tmp[tmp]
                * mod.tmp_weight[tmp]
                for (p, tmp) in mod.CARBON_CREDITS_PRJ_OPR_TMPS
                if mod.period[tmp] == prd and p == prj
            )
        )

    m.Project_Carbon_Credits_Generated_Constraint = Constraint(
        m.CARBON_CREDITS_PRJ_OPR_PRDS, rule=generated_credits_rule
    )


# Input-Output
###############################################################################


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
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
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        select=("project", "carbon_credits_zone"),
        param=(m.carbon_credits_zone,),
    )

    data_portal.data()["CARBON_CREDITS_PRJS"] = {
        None: list(data_portal.data()["carbon_credits_zone"].keys())
    }

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            subproblem,
            stage,
            "inputs",
            "project_carbon_credits.tab",
        ),
        param=(
            m.intensity_threshold_emissions_toCO2_per_MWh,
            m.absolute_threshold_emissions_toCO2,
        ),
    )


# Database
###############################################################################


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
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
    project_zones = c1.execute(
        f"""SELECT project, carbon_credits_zone
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        ) as prj_tbl
        LEFT OUTER JOIN 
        -- Get carbon credits zones for those projects
        (SELECT project, carbon_credits_zone
            FROM inputs_project_carbon_credits_zones
            WHERE project_carbon_credits_zone_scenario_id = {subscenarios.PROJECT_CARBON_CREDITS_ZONE_SCENARIO_ID}
        ) as prj_ct_zone_tbl
        USING (project)
        -- Filter out projects whose carbon credits zone is not one included in 
        -- our carbon_credits_zone_scenario_id
        WHERE carbon_credits_zone in (
                SELECT carbon_credits_zone
                    FROM inputs_geography_carbon_credits_zones
                    WHERE carbon_credits_zone_scenario_id = {subscenarios.CARBON_CREDITS_ZONE_SCENARIO_ID}
        );
        """
    )

    c2 = conn.cursor()
    project_carbon_credits = c2.execute(
        f"""SELECT project, period,
        intensity_threshold_emissions_toCO2_per_MWh,
        absolute_threshold_emissions_toCO2
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        ) as prj_fuels_tbl
        CROSS JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            ) as relevant_periods 
        LEFT OUTER JOIN
        -- Get carbon credits for those projects
            (SELECT project, period,
                intensity_threshold_emissions_toCO2_per_MWh,
                absolute_threshold_emissions_toCO2
            FROM inputs_project_carbon_credits
            WHERE project_carbon_credits_scenario_id = {subscenarios.PROJECT_CARBON_CREDITS_SCENARIO_ID}) as prj_ct_tbl
        USING (project, period)
        WHERE project in (
                SELECT project
                    FROM inputs_project_carbon_credits_zones
                    WHERE project_carbon_credits_zone_scenario_id = {subscenarios.PROJECT_CARBON_CREDITS_ZONE_SCENARIO_ID}
        );
        """
    )

    return project_zones, project_carbon_credits


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and write out the model input
    projects.tab (to be precise, amend it) and project_carbon_credits.tab files.
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
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(weather_iteration, hydro_iteration, subproblem, stage)

    project_zones, project_carbon_credits = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    # projects.tab
    # Make a dict for easy access
    prj_zone_dict = dict()
    for prj, zone in project_zones:
        prj_zone_dict[str(prj)] = "." if zone is None else str(zone)

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
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
        header.append("carbon_credits_zone")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_zone_dict.keys()):
                row.append(prj_zone_dict[row[0]])
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

    # project_carbon_credits.tab
    ct_df = cursor_to_df(project_carbon_credits)
    if not ct_df.empty:
        ct_df = ct_df.fillna(".")
        fpath = os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            subproblem,
            stage,
            "inputs",
            "project_carbon_credits.tab",
        )
        ct_df.to_csv(fpath, index=False, sep="\t")


def export_results(
    scenario_directory, weather_iteration, hydro_iteration, subproblem, stage, m, d
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
        "carbon_credits_zone",
        "carbon_credits_generated_tCO2",
    ]
    data = [
        [
            prj,
            prd,
            m.carbon_credits_zone[prj],
            value(m.Project_Carbon_Credits_Generated[prj, prd]),
        ]
        for (prj, prd) in m.CARBON_CREDITS_PRJ_OPR_PRDS
    ]

    results_df = create_results_df(
        index_columns=["project", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, PROJECT_PERIOD_DF)[c] = None
    getattr(d, PROJECT_PERIOD_DF).update(results_df)


# Validation
###############################################################################


def validate_inputs(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
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
    pass
