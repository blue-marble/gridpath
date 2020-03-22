#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load solver options and descriptions data
"""

from db.common_functions import spin_on_database_lock

def load_solver_options(io, c, solver_options_input, solver_descriptions_input):
    """
    solver options and decriptions
    :param io:
    :param c:
    :param solver_options_input:
    :param solver_descriptions_input:
    :return:
    """

    solver_options_input_data = []
    for i in solver_options_input.index:
        solver_options_input_data.append(
            (solver_options_input['solver_options_id'][i],
             solver_options_input['solver'][i],
             solver_options_input['solver_option_name'][i],
             solver_options_input['solver_option_value'][i])
        )

        inputs_sql = """
            INSERT OR IGNORE INTO options_solver_values 
            (solver_options_id, solver, solver_option_name, solver_option_value) 
            VALUES (?, ?, ?, ?)
            """
        spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=solver_options_input_data)

    solver_descriptions_input_data = []
    for i in solver_descriptions_input.index:
        solver_descriptions_input_data.append(
            (int(solver_descriptions_input['solver_options_id'][i]),
             solver_descriptions_input['name'][i],
             solver_descriptions_input['description'][i])
        )

        inputs_sql = """
            INSERT OR IGNORE INTO options_solver_descriptions 
            (solver_options_id, name, description) 
            VALUES (?, ?, ?)
            """
        spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=solver_descriptions_input_data)
