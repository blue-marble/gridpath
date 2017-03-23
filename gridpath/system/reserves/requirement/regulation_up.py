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
        "REGULATION_UP_ZONES",
        "REGULATION_UP_ZONE_TIMEPOINTS",
        "regulation_up_requirement_mw"
        )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, horizon, stage,
                            "regulation_up_requirement.tab",
                            "REGULATION_UP_ZONE_TIMEPOINTS",
                            "regulation_up_requirement_mw"
                            )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # regulation_up_requirement.tab
    with open(os.path.join(inputs_directory,
                           "regulation_up_requirement.tab"), "w") as \
            regulation_up_tab_file:
        writer = csv.writer(regulation_up_tab_file, delimiter="\t")

        # Write header
        # TODO: change these headers
        writer.writerow(
            ["LOAD_ZONES", "TIMEPOINTS", "upward_reserve_requirement"]
        )

        regulation_up = c.execute(
            """SELECT regulation_up_ba, timepoint, regulation_up_mw
            FROM inputs_system_regulation_up
            INNER JOIN
            (SELECT timepoint
            FROM inputs_temporal_timepoints
            WHERE timepoint_scenario_id = {}) as relevant_timepoints
            USING (timepoint)
            INNER JOIN
            (SELECT regulation_up_ba
            FROM inputs_geography_regulation_up_bas
            WHERE regulation_up_ba_scenario_id = {}) as relevant_bas
            USING (regulation_up_ba)
            WHERE regulation_up_scenario_id = {}
            """.format(
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.REGULATION_UP_BA_SCENARIO_ID,
                subscenarios.REGULATION_UP_SCENARIO_ID
            )
        )
        for row in regulation_up:
            writer.writerow(row)
