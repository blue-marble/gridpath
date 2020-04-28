#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import absolute_import

import csv
import os.path

from gridpath.system.reserves.requirement.reserve_requirements import \
    generic_get_inputs_from_database, generic_add_model_components, \
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
        reserve_zone_set="SPINNING_RESERVES_ZONES",
        reserve_zone_timepoint_set="SPINNING_RESERVES_ZONE_TIMEPOINTS",
        reserve_requirement_tmp_param="spinning_reserves_requirement_mw",
        reserve_requirement_percentage_param="spin_per_req",
        reserve_zone_load_zone_set="SPIN_BA_LZ",
        reserve_requirement_expression="Spin_Requirement"
        )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            "spinning_reserves_requirement.tab",
                            "SPINNING_RESERVES_ZONE_TIMEPOINTS",
                            "spinning_reserves_requirement_mw"
                            )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    return \
        generic_get_inputs_from_database(
            subscenarios=subscenarios,
            subproblem=subproblem, stage=stage, conn=conn,
            reserve_type="spinning_reserves",
            reserve_type_ba_subscenario_id
            =subscenarios.SPINNING_RESERVES_BA_SCENARIO_ID,
            reserve_type_req_subscenario_id
            =subscenarios.SPINNING_RESERVES_SCENARIO_ID
        )


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
    # spinning_reserves = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    spinning_reserves_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    spinning_reserves, _, _ = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # spinning_reserves_requirement.tab
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "spinning_reserves_requirement.tab"), "w", newline="") as \
            spinning_reserves_tab_file:
        writer = csv.writer(spinning_reserves_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["bas", "timepoints", "spinning_reserve_requirement"]
        )

        for row in spinning_reserves:
            writer.writerow(row)
