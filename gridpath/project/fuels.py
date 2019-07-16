#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import csv
import os.path
from pyomo.environ import Param, Set, NonNegativeReals


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


def load_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    fuels = c.execute(
        """SELECT fuel, co2_intensity_tons_per_mmbtu
        FROM inputs_project_fuels
        WHERE fuel_scenario_id = {}""".format(
            subscenarios.FUEL_SCENARIO_ID
        )
    ).fetchall()

    fuel_prices = c.execute(
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
    ).fetchall()

    return fuels, fuel_prices


def validate_inputs(subscenarios, subproblem, stage, c):
    """
    Load the inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    pass
    # Validation to be added
    # fuels, fuel_prices = load_inputs_from_database(
    #     subscenarios, subproblem, stage, c)


    # TODO: validate inputs and make sure that the fuels we have cover all the
    # fuels specified in projects_inputs_operational_chars

    # look at what fuels you're supposed to have (by looking at projects)
    # and then make sure you have data for all of them
    # fuels + fuel prices for the periods and months you are modeling

def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, c):
    """
    Load the inputs from database and write out the model input
    fuels.tab and fuel_prices.tab files.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    fuels, fuel_prices = load_inputs_from_database(
        subscenarios, subproblem, stage, c)

    with open(os.path.join(inputs_directory,
                           "fuels.tab"), "w") as \
            fuels_tab_file:
        writer = csv.writer(fuels_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["FUELS", "co2_intensity_tons_per_mmbtu"]
        )

        for row in fuels:
            writer.writerow(row)

    with open(os.path.join(inputs_directory,
                           "fuel_prices.tab"), "w") as \
            fuel_prices_tab_file:
        writer = csv.writer(fuel_prices_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["fuel", "period", "month", "fuel_price_per_mmbtu"]
        )

        for row in fuel_prices:
            writer.writerow(row)
