#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Validate a scenario based on input from the UI client.
"""

from gridpath import validate_inputs


def validate_scenario(db_path, client_message):
    """

    :param db_path:
    :param client_message:
    :return:
    """
    scenario_id = str(client_message['scenario'])
    validate_inputs.main(
      ["--database", db_path, "--scenario_id", scenario_id]
    )
