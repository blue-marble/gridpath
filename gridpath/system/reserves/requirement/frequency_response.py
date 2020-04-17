#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import absolute_import

import csv
import os.path
from pyomo.environ import Param, NonNegativeReals

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
        "FREQUENCY_RESPONSE_BAS",
        "FREQUENCY_RESPONSE_BA_TIMEPOINTS",
        "frequency_response_requirement_mw"
        )

    # Also add the partial requirement for frequency response that can be
    # met by only a subset of the projects that can provide frequency response

    m.frequency_response_requirement_partial_mw = Param(
        m.FREQUENCY_RESPONSE_BA_TIMEPOINTS,
        within=NonNegativeReals
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    
    :param m: 
    :param d: 
    :param data_portal: 
    :param scenario_directory: 
    :param stage:
    :param stage: 
    :return: 
    """
    # Don't use generic function from reserve_requirements.py, as we are
    # importing two columns (total and partial requirement), not just a
    # single param
    data_portal.load(filename=os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "frequency_response_requirement.tab"),
                     index=m.FREQUENCY_RESPONSE_BA_TIMEPOINTS,
                     param=(m.frequency_response_requirement_mw,
                            m.frequency_response_requirement_partial_mw)
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
    frequency_response = c.execute(
        """SELECT frequency_response_ba, timepoint, 
        frequency_response_mw, frequency_response_partial_mw
        FROM inputs_system_frequency_response
        INNER JOIN
        (SELECT timepoint 
        FROM inputs_temporal_timepoints
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}) as relevant_timepoints
        USING (timepoint)
        INNER JOIN
        (SELECT frequency_response_ba
        FROM inputs_geography_frequency_response_bas
        WHERE frequency_response_ba_scenario_id = {}) as relevant_bas
        USING (frequency_response_ba)
        WHERE frequency_response_scenario_id = {}
        AND stage_id = {}
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID,
            subscenarios.FREQUENCY_RESPONSE_SCENARIO_ID,
            stage
        )
    )

    return frequency_response


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
    # frequency_response = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    frequency_response_requirement.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    frequency_response = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "frequency_response_requirement.tab"), "w", newline="") as \
            frequency_response_tab_file:
        writer = csv.writer(frequency_response_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["ba", "timepoint", "requirement_mw", "partial_requirement_mw"]
        )

        for row in frequency_response:
            writer.writerow(row)
