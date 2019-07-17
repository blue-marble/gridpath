#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import absolute_import

import csv
import os.path

from .reserve_requirements import generic_add_model_components, \
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
        "LF_RESERVES_DOWN_ZONES",
        "LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
        "lf_reserves_down_requirement_mw"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            "lf_reserves_down_requirement.tab",
                            "LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
                            "lf_reserves_down_requirement_mw"
                            )


def get_inputs_from_database(subscenarios, subproblem, stage,
                             c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # lf_reserves_down_requirement.tab
    with open(os.path.join(inputs_directory,
                           "lf_reserves_down_requirement.tab"), "w") as \
            lf_reserves_down_tab_file:
        writer = csv.writer(lf_reserves_down_tab_file, delimiter="\t")

        # Write header
        # TODO: change these headers
        writer.writerow(
            ["LOAD_ZONES", "TIMEPOINTS", "downward_reserve_requirement"]
        )

        lf_reserves_down = c.execute(
            """SELECT lf_reserves_down_ba, timepoint, lf_reserves_down_mw
            FROM inputs_system_lf_reserves_down
            INNER JOIN
            (SELECT timepoint
            FROM inputs_temporal_timepoints
            WHERE temporal_scenario_id = {}
            AND subproblem_id = {}
            AND stage_id = {}) as relevant_timepoints
            USING (timepoint)
            INNER JOIN
            (SELECT lf_reserves_down_ba
            FROM inputs_geography_lf_reserves_down_bas
            WHERE lf_reserves_down_ba_scenario_id = {}) as relevant_bas
            USING (lf_reserves_down_ba)
            WHERE lf_reserves_down_scenario_id = {}
            AND stage_id = {}
            """.format(
                subscenarios.TEMPORAL_SCENARIO_ID,
                subproblem,
                stage,
                subscenarios.LF_RESERVES_DOWN_BA_SCENARIO_ID,
                subscenarios.LF_RESERVES_DOWN_SCENARIO_ID,
                stage
            )
        )
        for row in lf_reserves_down:
            writer.writerow(row)
