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

"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, NonNegativeReals, Reals, Any
from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_dtypes,
    get_expected_dtypes,
    validate_columns,
    validate_idxs,
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
    m.FUELS = Set()
    m.FUEL_GROUPS = Set()
    m.FUEL_GROUPS_FUELS = Set(within=m.FUEL_GROUPS * m.FUELS)
    m.FUELS_BY_FUEL_GROUP = Set(
        m.FUEL_GROUPS,
        within=m.FUELS,
        initialize=lambda mod, fg: [
            f for (group, f) in mod.FUEL_GROUPS_FUELS if group == fg
        ],
    )

    # Allow negative emissions
    m.co2_intensity_tons_per_mmbtu = Param(m.FUELS, within=Reals)

    m.fuel_price_per_mmbtu = Param(
        m.FUELS, m.PERIODS, m.MONTHS, within=NonNegativeReals
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
    :param stage:
    :param stage:
    :return:
    """
    # Load fuel chars only if there are data
    # There will be no data in this file if the database is used and there
    # are no projects with fuels in the scenario
    # Fuel group column is optional
    fuels_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "fuels.tab",
    )
    fuels_df = pd.read_csv(fuels_file, delimiter="\t")
    if not fuels_df.empty:
        data_portal.load(
            filename=fuels_file,
            index=m.FUELS,
            select=("fuel", "co2_intensity_tons_per_mmbtu"),
            param=m.co2_intensity_tons_per_mmbtu,
        )

        header = pd.read_csv(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "fuels.tab",
            ),
            sep="\t",
            header=None,
            nrows=1,
        ).values[0]

        if "fuel_group" in header:
            data_portal.data()["FUEL_GROUPS"] = fuels_df["fuel_group"].unique()

            data_portal.load(
                filename=fuels_file,
                index=m.FUEL_GROUPS_FUELS,
                select=("fuel_group", "fuel"),
                param=(),
            )

    # Load fuel prices only if there are data
    # There will be no data in this file if the database is used and there
    # are no projects with fuels in the scenario
    fuels_prices_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "fuel_prices.tab",
    )
    fuel_prices_df = pd.read_csv(fuels_prices_file)
    if not fuel_prices_df.empty:
        data_portal.load(filename=fuels_prices_file, param=m.fuel_price_per_mmbtu)


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
    fuels = c1.execute(
        """SELECT DISTINCT fuel, co2_intensity_tons_per_mmbtu, fuel_group
        FROM (
        SELECT project, fuel, min_fraction_in_fuel_blend, max_fraction_in_fuel_blend
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, project_fuel_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {opchar_scenario_id}
        ) AS op_char
        USING(project)
        -- select only heat curves of matching projects
        INNER JOIN
        inputs_project_fuels
        USING(project, project_fuel_scenario_id)
        -- Get only the subset of projects in the portfolio based on the 
        -- project_portfolio_scenario_id 
        WHERE project_portfolio_scenario_id = {portfolio_scenario_id}
        ) as project_fuels_tbl
        LEFT OUTER JOIN (
        -- Get the fuel chars for the relevant fuels
        SELECT fuel, co2_intensity_tons_per_mmbtu, fuel_group
        FROM inputs_fuels
        WHERE fuel_scenario_id = {fuel_scenario_id}
        ) AS fuels_tbl
        USING (fuel)
        -- Filter out the NULLs (from projects with no fuels)
        WHERE fuel NOT NULL
        ;
        """.format(
            opchar_scenario_id=subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            fuel_scenario_id=subscenarios.FUEL_SCENARIO_ID,
        )
    )

    c2 = conn.cursor()
    fuel_prices = c2.execute(
        """SELECT DISTINCT fuel, period, month, fuel_price_per_mmbtu
        FROM (
       SELECT project, fuel, min_fraction_in_fuel_blend, max_fraction_in_fuel_blend
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, project_fuel_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {opchar_scenario_id}
        ) AS op_char
        USING(project)
        -- select only heat curves of matching projects
        INNER JOIN
        inputs_project_fuels
        USING(project, project_fuel_scenario_id)
        -- Get only the subset of projects in the portfolio based on the 
        -- project_portfolio_scenario_id 
        WHERE project_portfolio_scenario_id = {portfolio_scenario_id}
        ) as project_fuels_tbl
        LEFT OUTER JOIN (
        -- Get the fuel chars for the relevant fuels
        SELECT fuel, period, month, fuel_price_per_mmbtu
        FROM inputs_fuel_prices
        WHERE fuel_price_scenario_id = {fuel_price_scenario_id}
        ) AS fuels_tbl
        USING (fuel)
        -- Only get periods in the relevant temporal_scenario_id
        INNER JOIN (
        SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal_scenario_id}
        ) as periods_tbl
        USING (period)
        -- Filter out the NULLs (from projects with no fuels)
        WHERE fuel NOT NULL
        ;
        """.format(
            opchar_scenario_id=subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            fuel_price_scenario_id=subscenarios.FUEL_PRICE_SCENARIO_ID,
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
        )
    )

    return fuels, fuel_prices


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

    # Get the fuel input data
    fuels, fuel_prices = get_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    # Get the projects fuels
    c1 = conn.cursor()
    projects = c1.execute(
        """
        SELECT project, fuel, min_fraction_in_fuel_blend, max_fraction_in_fuel_blend
        FROM inputs_project_portfolios
        -- select the correct operational characteristics subscenario
        INNER JOIN
        (SELECT project, project_fuel_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        ) AS op_char
        USING(project)
        -- select only heat curves of matching projects
        INNER JOIN
        inputs_project_fuels
        USING(project, project_fuel_scenario_id)
        -- Get only the subset of projects in the portfolio based on the 
        -- project_portfolio_scenario_id 
        WHERE project_portfolio_scenario_id = {}
        """.format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    # Get the relevant periods and months
    c2 = conn.cursor()
    periods_months = c2.execute(
        """SELECT DISTINCT period, month
        FROM inputs_temporal
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID, subproblem, stage
        )
    )

    # Convert input data into pandas DataFrame
    fuels_df = cursor_to_df(fuels)
    fuel_prices_df = cursor_to_df(fuel_prices)
    prj_df = cursor_to_df(projects)

    # Get relevant lists
    fuels = fuels_df["fuel"].to_list()
    actual_fuel_periods_months = list(
        fuel_prices_df[["fuel", "period", "month"]].itertuples(index=False, name=None)
    )
    req_fuel_periods_months = [(f, p, m) for (p, m) in periods_months for f in fuels]

    # Check data types
    expected_dtypes = get_expected_dtypes(conn, ["inputs_fuels", "inputs_fuel_prices"])

    dtype_errors, error_columns = validate_dtypes(fuels_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_fuels",
        severity="High",
        errors=dtype_errors,
    )

    dtype_errors, error_columns = validate_dtypes(fuel_prices_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_fuel_prices",
        severity="High",
        errors=dtype_errors,
    )

    # TODO: couldn't this be a simple foreign key or is NULL not allowed then?
    # TODO: should this check be in projects.init instead?
    # Check that fuels specified for projects are valid fuels
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_columns(prj_df, "fuel", valids=fuels),
    )

    # Check that fuel prices exist for the period and month
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_fuel_prices",
        severity="High",
        errors=validate_idxs(
            actual_idxs=actual_fuel_periods_months,
            req_idxs=req_fuel_periods_months,
            idx_label="(fuel, period, month)",
        ),
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
    fuels.tab and fuel_prices.tab files.
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

    fuels, fuel_prices = get_inputs_from_database(
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
            "fuels.tab",
        ),
        "w",
        newline="",
    ) as fuels_tab_file:
        writer = csv.writer(fuels_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["fuel", "co2_intensity_tons_per_mmbtu", "fuel_group"])

        for row in fuels:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "fuel_prices.tab",
        ),
        "w",
        newline="",
    ) as fuel_prices_tab_file:
        writer = csv.writer(fuel_prices_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["fuel", "period", "month", "fuel_price_per_mmbtu"])

        for row in fuel_prices:
            writer.writerow(row)
