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
        reserve_zone_set="REGULATION_DOWN_ZONES",
        reserve_zone_timepoint_set="REGULATION_DOWN_ZONE_TIMEPOINTS",
        reserve_requirement_tmp_param="regulation_down_requirement_mw",
        reserve_requirement_percentage_param="reg_down_per_req",
        reserve_zone_load_zone_set="REG_DOWN_BA_LZ",
        reserve_requirement_expression="Reg_Down_Requirement"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            "regulation_down_requirement.tab",
                            "REGULATION_DOWN_ZONE_TIMEPOINTS",
                            "regulation_down_requirement_mw"
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
    regulation_down = c.execute(
        """SELECT regulation_down_ba, timepoint, regulation_down_mw
        FROM inputs_system_regulation_down
        INNER JOIN
        (SELECT timepoint 
        FROM inputs_temporal_timepoints
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}) as relevant_timepoints
        USING (timepoint)
        INNER JOIN
        (SELECT regulation_down_ba
        FROM inputs_geography_regulation_down_bas
        WHERE regulation_down_ba_scenario_id = {}) as relevant_bas
        USING (regulation_down_ba)
        WHERE regulation_down_scenario_id = {}
        AND stage_id = {}
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.REGULATION_DOWN_BA_SCENARIO_ID,
            subscenarios.REGULATION_DOWN_SCENARIO_ID,
            stage
        )
    )

    return regulation_down


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
    # regulation_down = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    regulation_down_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    regulation_down = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "regulation_down_requirement.tab"), "w", newline="") as \
            regulation_down_tab_file:
        writer = csv.writer(regulation_down_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        # TODO: change these headers
        writer.writerow(
            ["LOAD_ZONES", "timepoint", "downward_reserve_requirement"]
        )

        for row in regulation_down:
            writer.writerow(row)
