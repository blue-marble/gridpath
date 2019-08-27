#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, NonNegativeReals
from gridpath.auxiliary.auxiliary import check_dtypes, \
    write_validation_to_database


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.FUELS = Set()
    m.co2_intensity_tons_per_mmbtu = Param(m.FUELS, within=NonNegativeReals)

    m.fuel_price_per_mmbtu = Param(m.FUELS, m.PERIODS, m.MONTHS,
                                   within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param stage:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "fuels.tab"),
                     index=m.FUELS,
                     select=("FUELS",
                             "co2_intensity_tons_per_mmbtu"),
                     param=m.co2_intensity_tons_per_mmbtu
                     )

    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "fuel_prices.tab"),
                     select=("fuel", "period", "month",
                             "fuel_price_per_mmbtu"),
                     param=m.fuel_price_per_mmbtu
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c1 = conn.cursor()
    fuels = c1.execute(
        """SELECT fuel, co2_intensity_tons_per_mmbtu
        FROM inputs_project_fuels
        WHERE fuel_scenario_id = {}""".format(
            subscenarios.FUEL_SCENARIO_ID
        )
    )

    c2 = conn.cursor()
    fuel_prices = c2.execute(
        """SELECT fuel, period, month, fuel_price_per_mmbtu
        FROM inputs_project_fuel_prices
        INNER JOIN
        (SELECT period from inputs_temporal_periods
        WHERE temporal_scenario_id = {})
        USING (period)
        WHERE fuel_price_scenario_id = {}""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.FUEL_PRICE_SCENARIO_ID
        )
    )

    return fuels, fuel_prices


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    validation_results = []

    # Get the fuel input data
    fuels, fuel_prices = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Get the projects fuels
    c1 = conn.cursor()
    projects = c1.execute(
        """SELECT project, fuel
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, fuel
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) AS op_char
        USING (project)
        WHERE project_portfolio_scenario_id = {}""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    # Get the relevant periods and months
    c2 = conn.cursor()
    periods_months = c2.execute(
        """SELECT DISTINCT period, month
        FROM inputs_temporal_timepoints
        LEFT OUTER JOIN
        (SELECT horizon, month
        FROM inputs_temporal_horizons
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {})
        USING (horizon)
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID, subproblem,
            subscenarios.TEMPORAL_SCENARIO_ID, subproblem, stage
        )
    ).fetchall()

    # Convert input data into pandas DataFrame
    fuels_df = pd.DataFrame(
        data=fuels.fetchall(),
        columns=[s[0] for s in fuels.description]
    )
    fuel_prices_df = pd.DataFrame(
        data=fuel_prices.fetchall(),
        columns = [s[0] for s in fuel_prices.description]
    )
    prj_df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )

    # Check data types fuels:
    expected_dtypes = {
        "fuel": "string",
        "co2_intensity_tons_per_mmbtu": "numeric"
    }
    dtype_errors, error_columns = check_dtypes(fuels_df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             __name__,
             "PROJECT_FUELS",
             "inputs_project_fuels",
             "Invalid data type",
             error
             )
        )

    # Check data types fuel prices:
    expected_dtypes = {
        "fuel": "string",
        "period": "numeric",
        "month": "numeric",
        "fuel_price_per_mmbtu": "numeric"
    }
    dtype_errors, error_columns = check_dtypes(fuel_prices_df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             __name__,
             "PROJECT_FUEL_PRICES",
             "inputs_project_fuel_prices",
             "Invalid data type",
             error
             )
        )

    # Check that fuels specified for projects exist in fuels table
    validation_errors = validate_fuel_projects(prj_df, fuels_df)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Non existent fuel",
             error)
        )

    # Check that fuel prices exist for the period and month
    validation_errors = validate_fuel_prices(fuels_df, fuel_prices_df,
                                             periods_months)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             __name__,
             "PROJECT_FUEL_PRICES",
             "inputs_project_fuel_prices",
             "Missing fuel price",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)


def validate_fuel_projects(prj_df, fuels_df):
    """
    Check that fuels specified for projects exist in fuels table
    :param prj_df:
    :param fuels_df:
    :return:
    """
    results = []
    fuel_mask = pd.notna(prj_df["fuel"])
    existing_fuel_mask = prj_df["fuel"].isin(fuels_df["fuel"])
    invalids = fuel_mask & ~existing_fuel_mask
    if invalids.any():
        bad_projects = prj_df["project"][invalids].values
        bad_fuels = prj_df["fuel"][invalids].values
        print_bad_projects = ", ".join(bad_projects)
        print_bad_fuels = ", ".join(bad_fuels)
        results.append(
            "Project(s) '{}': Specified fuel(s) '{}' do(es) not exist"
            .format(print_bad_projects, print_bad_fuels)
        )

    return results


def validate_fuel_prices(fuels_df, fuel_prices_df, periods_months):
    """
    Check that fuel prices exist for the period and month
    :param fuels_df:
    :param fuel_prices_df:
    :param periods_months:
    :return:
    """
    results = []
    for f in fuels_df["fuel"].values:
        df = fuel_prices_df[fuel_prices_df["fuel"] == f]
        for period, month in periods_months:
            if not ((df.period == period) & (df.month == month)).any():
                results.append(
                    "Fuel '{}': Missing price for period '{}', month '{}'"
                    .format(f, str(period), str(month))
                )

    return results


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    fuels.tab and fuel_prices.tab files.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    fuels, fuel_prices = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "fuels.tab"), "w", newline="") as \
            fuels_tab_file:
        writer = csv.writer(fuels_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["FUELS", "co2_intensity_tons_per_mmbtu"]
        )

        for row in fuels:
            writer.writerow(row)

    with open(os.path.join(inputs_directory,
                           "fuel_prices.tab"), "w", newline="") as \
            fuel_prices_tab_file:
        writer = csv.writer(fuel_prices_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["fuel", "period", "month", "fuel_price_per_mmbtu"]
        )

        for row in fuel_prices:
            writer.writerow(row)
