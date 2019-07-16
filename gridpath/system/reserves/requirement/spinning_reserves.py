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
        "SPINNING_RESERVES_ZONES",
        "SPINNING_RESERVES_ZONE_TIMEPOINTS",
        "spinning_reserves_requirement_mw"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            "spinning_reserves_requirement.tab",
                            "SPINNING_RESERVES_ZONE_TIMEPOINTS",
                            "spinning_reserves_requirement_mw"
                            )


def load_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    spinning_reserves = c.execute(
        """SELECT spinning_reserves_ba, timepoint, spinning_reserves_mw
        FROM inputs_system_spinning_reserves
        INNER JOIN
        (SELECT timepoint
        FROM inputs_temporal_timepoints
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}) as relevant_timepoints
        USING (timepoint)
        INNER JOIN
        (SELECT spinning_reserves_ba
        FROM inputs_geography_spinning_reserves_bas
        WHERE spinning_reserves_ba_scenario_id = {}) as relevant_bas
        USING (spinning_reserves_ba)
        WHERE spinning_reserves_scenario_id = {}
        AND stage_id = {}
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.SPINNING_RESERVES_BA_SCENARIO_ID,
            subscenarios.SPINNING_RESERVES_SCENARIO_ID,
            stage
        )
    )

    return spinning_reserves


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
    # spinning_reserves = load_inputs_from_database(
    #     subscenarios, subproblem, stage, c)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, c):
    """
    Load the inputs from database and write out the model input
    spinning_reserves_requirement.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    spinning_reserves = load_inputs_from_database(
        subscenarios, subproblem, stage, c)

    # spinning_reserves_requirement.tab
    with open(os.path.join(inputs_directory,
                           "spinning_reserves_requirement.tab"), "w") as \
            spinning_reserves_tab_file:
        writer = csv.writer(spinning_reserves_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["bas", "timepoints", "spinning_reserve_requirement"]
        )

        for row in spinning_reserves:
            writer.writerow(row)
