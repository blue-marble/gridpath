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
        m=m,
        d=d,
        reserve_zone_set="LF_RESERVES_UP_ZONES",
        reserve_zone_timepoint_set="LF_RESERVES_UP_ZONE_TIMEPOINTS",
        reserve_requirement_tmp_param="lf_reserves_up_requirement_mw",
        reserve_requirement_percentage_param="lf_up_per_req",
        reserve_zone_load_zone_set="LF_UP_BA_LZ",
        reserve_requirement_expression="LF_Up_Requirement"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            "lf_reserves_up_requirement.tab",
                            "LF_RESERVES_UP_ZONE_TIMEPOINTS",
                            "lf_reserves_up_requirement_mw"
                            )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    lf_reserves_up = c.execute(
        """SELECT lf_reserves_up_ba, timepoint, lf_reserves_up_mw
        FROM inputs_system_lf_reserves_up
        INNER JOIN
        (SELECT timepoint
        FROM inputs_temporal_timepoints
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}) as relevant_timepoints
        USING (timepoint)
        INNER JOIN
        (SELECT lf_reserves_up_ba
        FROM inputs_geography_lf_reserves_up_bas
        WHERE lf_reserves_up_ba_scenario_id = {}) as relevant_bas
        USING (lf_reserves_up_ba)
        WHERE lf_reserves_up_scenario_id = {}
        AND stage_id = {}
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.LF_RESERVES_UP_BA_SCENARIO_ID,
            subscenarios.LF_RESERVES_UP_SCENARIO_ID,
            stage
        )
    )

    return lf_reserves_up


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # lf_reserves_up = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    lf_reserves_up_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    lf_reserves_up = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "lf_reserves_up_requirement.tab"), "w", newline="") as \
            lf_reserves_up_tab_file:
        writer = csv.writer(lf_reserves_up_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        # TODO: change these headers
        writer.writerow(
            ["LOAD_ZONES", "timepoint", "upward_reserve_requirement"]
        )

        for row in lf_reserves_up:
            writer.writerow(row)
