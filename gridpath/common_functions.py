#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import os.path

# If the user has specified a path where to create the scenario directory,
# use that; otherwise, default to a directory called 'scenarios' in the
# GridPath root directory to find the scenario directory


def determine_scenario_directory(scenario_location, scenario_name):
    """
    :param scenario_location: string, the base directory
    :param scenario_name: string, the scenario name
    :return: the scenario directory (string)

    Determine the scenario directory given a base directory and the scenario
    name.
    """
    if scenario_location is None:
        main_directory = os.path.join(
            os.getcwd(), "..", "scenarios")
    else:
        main_directory = scenario_location

    scenario_directory = os.path.join(
        main_directory, str(scenario_name)
    )

    return scenario_directory


def create_directory_if_not_exists(directory):
    """
    :param directory:

    Check if a directory exists and create it if not.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

