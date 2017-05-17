#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path

from reserve_requirements import generic_add_model_components, \
    generic_load_model_data


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "SPINNING_RESERVES_ZONES",
        "SPINNING_RESERVES_ZONE_TIMEPOINTS",
        "spinning_reserves_requirement_mw"
        )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, horizon, stage,
                            "spinning_reserves_requirement.tab",
                            "SPINNING_RESERVES_ZONE_TIMEPOINTS",
                            "spinning_reserves_requirement_mw"
                            )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # spinning_reserves_requirement.tab
    with open(os.path.join(inputs_directory,
                           "spinning_reserves_requirement.tab"), "w") as \
            spinning_reserves_tab_file:
        writer = csv.writer(spinning_reserves_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["bas", "timepoints", "spinning_reserve_requirement"]
        )

        spinning_reserves = c.execute(
            """SELECT spinning_reserves_ba, timepoint, spinning_reserves_mw
            FROM inputs_system_spinning_reserves
            INNER JOIN
            (SELECT timepoint
            FROM inputs_temporal_timepoints
            WHERE timepoint_scenario_id = {}) as relevant_timepoints
            USING (timepoint)
            INNER JOIN
            (SELECT spinning_reserves_ba
            FROM inputs_geography_spinning_reserves_bas
            WHERE spinning_reserves_ba_scenario_id = {}) as relevant_bas
            USING (spinning_reserves_ba)
            WHERE spinning_reserves_scenario_id = {}
            """.format(
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.SPINNING_RESERVES_BA_SCENARIO_ID,
                subscenarios.SPINNING_RESERVES_SCENARIO_ID
            )
        )
        for row in spinning_reserves:
            writer.writerow(row)
