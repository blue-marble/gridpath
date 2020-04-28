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
        reserve_zone_set="LF_RESERVES_DOWN_ZONES",
        reserve_zone_timepoint_set="LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
        reserve_requirement_tmp_param="lf_reserves_down_requirement_mw",
        reserve_requirement_percentage_param="lf_down_per_req",
        reserve_zone_load_zone_set="LF_DOWN_BA_LZ",
        reserve_requirement_expression="LF_Down_Requirement"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            "lf_reserves_down_requirement.tab",
                            "LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
                            "lf_reserves_down_requirement_mw"
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
    lf_reserves_down_tmp = c.execute(
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

    c2 = conn.cursor()
    # Get any percentage requirement
    percentage_req = c2.execute("""
        SELECT lf_reserves_down_ba, percent_load_req
        FROM inputs_system_lf_reserves_down_percentage
        WHERE lf_reserves_down_scenario_id = {}
        """.format(subscenarios.LF_RESERVES_DOWN_SCENARIO_ID)
    )

    # Get any reserve zone to load zone mapping for the percent target
    c3 = conn.cursor()
    lz_mapping = c3.execute(
        """SELECT lf_reserves_down_ba, load_zone
        FROM inputs_system_lf_reserves_down_percentage_lz_map
        JOIN
        (SELECT lf_reserves_down_ba
        FROM inputs_geography_lf_reserves_down_bas
        WHERE lf_reserves_down_ba_scenario_id = {}) as relevant_bas
        USING (lf_reserves_down_ba)
        WHERE lf_reserves_down_scenario_id = {}
        """.format(
            subscenarios.LF_RESERVES_DOWN_BA_SCENARIO_ID,
            subscenarios.LF_RESERVES_DOWN_SCENARIO_ID
        )
    )

    return lf_reserves_down_tmp, percentage_req, lz_mapping


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
    # lf_reserves_down = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    lf_reserves_down_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    lf_reserves_down, _, _ = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "lf_reserves_down_requirement.tab"), "w", newline="") as \
            lf_reserves_down_tab_file:
        writer = csv.writer(lf_reserves_down_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        # TODO: change these headers
        writer.writerow(
            ["LOAD_ZONES", "timepoint", "downward_reserve_requirement"]
        )

        for row in lf_reserves_down:
            writer.writerow(row)
