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
    m.fuel_price_per_mmbtu = Param(m.FUELS, within=NonNegativeReals)
    m.co2_intensity_tons_per_mmbtu = Param(m.FUELS, within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "fuels.tab"),
                     index=m.FUELS,
                     select=("FUELS", "fuel_price_per_mmbtu",
                             "co2_intensity_tons_per_mmbtu"),
                     param=(m.fuel_price_per_mmbtu,
                            m.co2_intensity_tons_per_mmbtu)
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # fuels.tab
    with open(os.path.join(inputs_directory,
                           "fuels.tab"), "w") as \
            fuels_tab_file:
        writer = csv.writer(fuels_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["FUELS", "fuel_price_per_mmbtu", "co2_intensity_tons_per_mmbtu"]
        )

        fuels = c.execute(
            """SELECT fuel, fuel_price_per_mmbtu, co2_intensity_tons_per_mmbtu
            FROM inputs_project_fuels
            WHERE fuel_scenario_id = {}""".format(
                subscenarios.FUEL_SCENARIO_ID
            )
        )
        for row in fuels:
            writer.writerow(row)
