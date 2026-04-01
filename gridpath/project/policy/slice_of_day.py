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
Slice-of-day capacity contribution for each project, zone, period, month, and
hour. The contribution is cap_fac[g, z, p, mn, hr] * Capacity_MW[g, p].
"""

import csv
import os.path
from pyomo.environ import Set, Param, Expression, NonNegativeReals, value

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

    m.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS = Set(dimen=5)

    m.slice_of_day_cap_fac = Param(
        m.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS, within=NonNegativeReals
    )

    m.SLICE_OF_DAY_PRJS_BY_ZONE = Set(
        m.SLICE_OF_DAY_ZONES,
        initialize=lambda mod, z: list(
            set(
                g
                for (g, zone, p, mn, hr) in mod.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
                if zone == z
            )
        ),
    )

    def slice_of_day_contribution_rule(mod, g, z, p, mn, hr):
        return mod.slice_of_day_cap_fac[g, z, p, mn, hr] * mod.Capacity_MW[g, p]

    m.Slice_of_Day_Contribution_MW = Expression(
        m.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS, rule=slice_of_day_contribution_rule
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
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "project_slice_of_day_contributions.tab",
        ),
        index=m.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS,
        param=m.slice_of_day_cap_fac,
        select=(
            "project",
            "slice_of_day_zone",
            "period",
            "sod_month",
            "sod_hour",
            "cap_fac",
        ),
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
    contributions = c.execute(
        """SELECT project, slice_of_day_zone, period, sod_month, sod_hour, cap_fac
        FROM inputs_project_slice_of_day_contributions
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal}) as relevant_periods
        USING (period)
        JOIN
        (SELECT slice_of_day_zone
        FROM inputs_geography_slice_of_day_zones
        WHERE slice_of_day_zone_scenario_id = {sod_zone}) as relevant_zones
        USING (slice_of_day_zone)
        WHERE project_slice_of_day_scenario_id = {sod_scenario};
        """.format(
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            sod_zone=subscenarios.SLICE_OF_DAY_ZONE_SCENARIO_ID,
            sod_scenario=subscenarios.PROJECT_SLICE_OF_DAY_SCENARIO_ID,
        )
    )

    return contributions


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
    pass
    # Validation to be added
    # contributions = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


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
    project_slice_of_day_contributions.tab file.
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

    contributions = get_inputs_from_database(
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
            "project_slice_of_day_contributions.tab",
        ),
        "w",
        newline="",
    ) as contributions_tab_file:
        writer = csv.writer(
            contributions_tab_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            ["project", "slice_of_day_zone", "period", "sod_month", "sod_hour", "cap_fac"]
        )

        for row in contributions:
            writer.writerow(row)


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
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_slice_of_day_contributions.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(
            [
                "project",
                "slice_of_day_zone",
                "period",
                "sod_month",
                "sod_hour",
                "cap_fac",
                "capacity_mw",
                "slice_of_day_contribution_mw",
            ]
        )
        for (g, z, p, mn, hr) in sorted(m.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS):
            writer.writerow(
                [
                    g,
                    z,
                    p,
                    mn,
                    hr,
                    value(m.slice_of_day_cap_fac[g, z, p, mn, hr]),
                    value(m.Capacity_MW[g, p]),
                    value(m.Slice_of_Day_Contribution_MW[g, z, p, mn, hr]),
                ]
            )


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
        which_results="project_slice_of_day_contributions",
    )
