#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Update scenario settings.
"""
from __future__ import print_function


def update_scenario_multiple_columns(
        io, c,
        scenario_name,
        column_values_dict
):
    """

    :param io:
    :param c:
    :param scenario_name:
    :param column_values_dict:
    :return:
    """
    for column_name in column_values_dict:
        update_scenario_single_column(
            io=io,
            c=c,
            scenario_name=scenario_name,
            column_name=column_name,
            column_value=column_values_dict[column_name]
        )

    io.commit()


def update_scenario_single_column(
        io, c,
        scenario_name,
        column_name,
        column_value
):
    """

    :param io:
    :param c:
    :param scenario_name:
    :param column_name:
    :param column_value:
    :return:
    """
    c.execute(
        """UPDATE scenarios
        SET {} = {}
        WHERE scenario_name = '{}';""".format(
            column_name, column_value, scenario_name
        )
    )

    io.commit()
