#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.transmission.capacity.capacity_types** package contains
modules to describe the various ways in which transmission-line capacity can be
treated in the optimization problem, e.g. as specified, available to be
built, available to be retired, etc.
"""

import pandas as pd
import os.path

from gridpath.auxiliary.auxiliary import load_tx_capacity_type_modules


def get_required_capacity_type_modules(subscenarios, c):
    """
    Get the required tx capacity type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    tx capacity types in the scenario's portfolio. Get the list based
    on the project_operational_chars_scenario_id of the scenario_id.

    This list will be used to know for which tx capacity type submodules we
    should validate inputs, get inputs from database, or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.

    :param subscenarios: SubScenarios object with all subscenario info
    :param c: database cursor
    :return: List of the required tx capacity type submodules
    """

    required_tx_capacity_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT capacity_type
            FROM inputs_transmission_portfolios
            LEFT OUTER JOIN
            (SELECT transmission_line, load_zone_from, load_zone_to
            FROM inputs_transmission_load_zones
            WHERE load_zone_scenario_id = {}
            AND transmission_load_zone_scenario_id = {}) as tx_load_zones
            USING (transmission_line)
            INNER JOIN
            (SELECT transmission_line
            FROM inputs_transmission_operational_chars
            WHERE transmission_operational_chars_scenario_id = {})
            USING (transmission_line)
            WHERE transmission_portfolio_scenario_id = {};""".format(
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.TRANSMISSION_LOAD_ZONE_SCENARIO_ID,
                subscenarios.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID,
                subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
            )
        ).fetchall()
    ]

    return required_tx_capacity_modules


def validate_inputs(subscenarios, subproblem, stage, c):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    # Load in the required tx capacity type modules
    scenario_id = subscenarios.SCENARIO_ID
    required_capacity_type_modules = get_required_capacity_type_modules(
        subscenarios, c)
    imported_capacity_type_modules = load_tx_capacity_type_modules(
            required_capacity_type_modules)

    # Validate module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "validate_module_specific_inputs"):
            imported_capacity_type_modules[op_m]. \
                validate_module_specific_inputs(
                    subscenarios, subproblem, stage, c)
        else:
            pass


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, c):
    """
    Get inputs from database and write out the model input .tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    # Load in the required capacity type modules
    required_capacity_type_modules = get_required_capacity_type_modules(
        subscenarios, c)
    imported_capacity_type_modules = load_tx_capacity_type_modules(
            required_capacity_type_modules)

    # Write module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "write_module_specific_model_inputs"):
            imported_capacity_type_modules[op_m]. \
                write_module_specific_model_inputs(
                    inputs_directory, subscenarios, subproblem, stage, c
            )
        else:
            pass
