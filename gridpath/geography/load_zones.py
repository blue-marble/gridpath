#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.geography.load_zones** module describes the geographic unit
at which load is met.
"""

import csv
import os.path
from pyomo.environ import Set


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the dynamic inputs class object; not used here

    The module adds the *LOAD_ZONES* set to the model formulation.

    We will designate the *LOAD_ZONES* set with *Z* and the load zones index
    will be *z*.
    """
    m.LOAD_ZONES = Set()


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
    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           "load_zones.tab"),
                     select=("load_zone",),
                     index=m.LOAD_ZONES,
                     param=()
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # TODO: we get the overgen and unserve energy penalties here, but they
    #  are loaded into the model in the load_balance system module
    # load_zones.tab
    with open(os.path.join(inputs_directory, "load_zones.tab"), "w") as \
            load_zones_tab_file:
        writer = csv.writer(load_zones_tab_file, delimiter="\t")

        # Write header
        writer.writerow(["load_zone", "overgeneration_penalty_per_mw",
                         "unserved_energy_penalty_per_mw"])

        load_zones = c.execute(
            """SELECT load_zone, overgeneration_penalty_per_mw,
               unserved_energy_penalty_per_mw
               FROM inputs_geography_load_zones
               WHERE load_zone_scenario_id = {};""".format(
                subscenarios.LOAD_ZONE_SCENARIO_ID
            )
        ).fetchall()

        for row in load_zones:
            writer.writerow(row)
