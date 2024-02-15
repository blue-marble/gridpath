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
Balancing areas where fuel constraints are enforced; these can be different from the
load zones and other balancing areas. Note that these are also differentiated by fuel.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Boolean, NonNegativeReals

from gridpath.auxiliary.db_interface import directories_to_db_values


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

    m.FUEL_BURN_LIMIT_BAS = Set(dimen=2)  # fuel and BA

    m.fuel_burn_min_allow_violation = Param(
        m.FUEL_BURN_LIMIT_BAS, within=Boolean, default=0
    )
    m.fuel_burn_min_violation_penalty_per_unit = Param(
        m.FUEL_BURN_LIMIT_BAS, within=NonNegativeReals, default=0
    )

    m.fuel_burn_max_allow_violation = Param(
        m.FUEL_BURN_LIMIT_BAS, within=Boolean, default=0
    )
    m.fuel_burn_max_violation_penalty_per_unit = Param(
        m.FUEL_BURN_LIMIT_BAS, within=NonNegativeReals, default=0
    )

    m.fuel_burn_relative_max_allow_violation = Param(
        m.FUEL_BURN_LIMIT_BAS, within=Boolean, default=0
    )
    m.fuel_burn_relative_max_violation_penalty_per_unit = Param(
        m.FUEL_BURN_LIMIT_BAS, within=NonNegativeReals, default=0
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
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "fuel_burn_limit_balancing_areas.tab",
        ),
        index=m.FUEL_BURN_LIMIT_BAS,
        param=(
            m.fuel_burn_min_allow_violation,
            m.fuel_burn_min_violation_penalty_per_unit,
            m.fuel_burn_max_allow_violation,
            m.fuel_burn_max_violation_penalty_per_unit,
            m.fuel_burn_relative_max_allow_violation,
            m.fuel_burn_relative_max_violation_penalty_per_unit,
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
    fuel_burn_limit_bas = c.execute(
        """SELECT fuel, fuel_burn_limit_ba, min_allow_violation, 
        min_violation_penalty_per_unit, max_allow_violation, 
        max_violation_penalty_per_unit, relative_max_allow_violation, 
        relative_max_violation_penalty_per_unit
        FROM inputs_geography_fuel_burn_limit_balancing_areas
        WHERE fuel_burn_limit_ba_scenario_id = {fuel_burn_limit_ba_scenario_id}
        AND fuel in (
        SELECT DISTINCT fuel
        FROM inputs_project_fuels
        WHERE (project, project_fuel_scenario_id) in (
            SELECT DISTINCT project, project_fuel_scenario_id
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {project_operational_chars_scenario_id}
            AND project in (
            SELECT DISTINCT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {project_portfolio_scenario_id}
            )
        )
        );
        """.format(
            fuel_burn_limit_ba_scenario_id=subscenarios.FUEL_BURN_LIMIT_BA_SCENARIO_ID,
            project_operational_chars_scenario_id=subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            project_portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    return fuel_burn_limit_bas


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
    carbon_cap_zones.tab file.
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

    fuel_burn_limit_bas = get_inputs_from_database(
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
            "fuel_burn_limit_balancing_areas.tab",
        ),
        "w",
        newline="",
    ) as tab_file:
        writer = csv.writer(tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "fuel",
                "fuel_burn_limit_ba",
                "min_allow_violation",
                "min_violation_penalty_per_unit",
                "max_allow_violation",
                "max_violation_penalty_per_unit",
                "relative_max_allow_violation",
                "relative_max_violation_penalty_per_unit",
            ]
        )

        for row in fuel_burn_limit_bas:
            writer.writerow(row)
