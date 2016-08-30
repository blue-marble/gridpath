#!/usr/bin/env python

"""

"""

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


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
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