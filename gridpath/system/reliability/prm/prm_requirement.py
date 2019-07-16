#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
PRM requirement for each PRM zone
"""

import csv
import os.path

from pyomo.environ import Set, Param, NonNegativeReals


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.PRM_ZONE_PERIODS_WITH_REQUIREMENT = \
        Set(dimen=2, within=m.PRM_ZONES * m.PERIODS)
    m.prm_requirement_mw = Param(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "prm_requirement.tab"),
                     index=m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
                     param=m.prm_requirement_mw,
                     select=("prm_zone", "period",
                             "prm_requirement_mw")
                     )


def load_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    prm_requirement = c.execute(
        """SELECT prm_zone, period, prm_requirement_mw
        FROM inputs_system_prm_requirement
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        USING (period)
        JOIN
        (SELECT prm_zone
        FROM inputs_geography_prm_zones
        WHERE prm_zone_scenario_id = {}) as relevant_zones
        using (prm_zone)
        WHERE prm_requirement_scenario_id = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.PRM_REQUIREMENT_SCENARIO_ID
        )
    )

    return prm_requirement


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
    # prm_requirement = load_inputs_from_database(
    #     subscenarios, subproblem, stage, c)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, c):
    """
    Load the inputs from database and write out the model input
    prm_requirement.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    prm_requirement = load_inputs_from_database(
        subscenarios, subproblem, stage, c)

    with open(os.path.join(inputs_directory,
                           "prm_requirement.tab"), "w") as \
            prm_requirement_tab_file:
        writer = csv.writer(prm_requirement_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["prm_zone", "period", "prm_requirement_mw"]
        )

        for row in prm_requirement:
            writer.writerow(row)
