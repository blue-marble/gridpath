#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path

from reserve_requirements import generic_add_model_components, \
    generic_load_model_data, generic_export_results, generic_save_duals


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "LF_RESERVES_UP_ZONES",
        "lf_reserves_up_zone",
        "LF_RESERVES_UP_ZONE_TIMEPOINTS",
        "LF_Reserves_Up_Violation_MW",
        "lf_reserves_up_violation_penalty_per_mw",
        "lf_reserves_up_requirement_mw",
        "LF_RESERVES_UP_PROJECTS",
        "Provide_LF_Reserves_Up_MW",
        "Total_LF_Reserves_Up_Provision_MW",
        "Meet_LF_Reserves_Up_Constraint",
        "LF_Reserves_Up_Penalty_Costs"
        )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, horizon, stage,
                            "load_following_up_balancing_areas.tab",
                            "lf_reserves_up_violation_penalty_per_mw",
                            "lf_reserves_up_requirement.tab",
                            "LF_RESERVES_UP_ZONE_TIMEPOINTS",
                            "lf_reserves_up_requirement_mw"
                            )


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    generic_export_results(scenario_directory, horizon, stage, m, d,
                           "lf_reserves_up_violation.csv",
                           "lf_reserves_up_violation_mw",
                           "LF_RESERVES_UP_ZONE_TIMEPOINTS",
                           "LF_Reserves_Up_Violation_MW"
                           )


def save_duals(m):
    """

    :param m:
    :return:
    """
    generic_save_duals(m, "Meet_LF_Reserves_Up_Constraint")


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # lf_reserves_up_requirement.tab
    with open(os.path.join(inputs_directory,
                           "lf_reserves_up_requirement.tab"), "w") as \
            lf_reserves_up_tab_file:
        writer = csv.writer(lf_reserves_up_tab_file, delimiter="\t")

        # Write header
        # TODO: change these headers
        writer.writerow(
            ["LOAD_ZONES", "TIMEPOINTS", "upward_reserve_requirement"]
        )

        lf_reserves_up = c.execute(
            """SELECT lf_reserves_up_ba, timepoint, lf_reserves_up_mw
            FROM lf_reserves_up
            WHERE period_scenario_id = {}
            AND horizon_scenario_id = {}
            AND timepoint_scenario_id = {}
            AND existing_project_scenario_id = {}
            AND new_project_scenario_id = {}
            AND lf_reserves_up_ba_scenario_id = {}
            AND lf_reserves_up_scenario_id = {}
            """.format(
                subscenarios.PERIOD_SCENARIO_ID,
                subscenarios.HORIZON_SCENARIO_ID,
                subscenarios.TIMEPOINT_SCENARIO_ID,
                subscenarios.EXISTING_PROJECT_SCENARIO_ID,
                subscenarios.NEW_PROJECT_SCENARIO_ID,
                subscenarios.LF_RESERVES_UP_BA_SCENARIO_ID,
                subscenarios.LF_RESERVES_UP_SCENARIO_ID
            )
        )
        for row in lf_reserves_up:
            writer.writerow(row)
