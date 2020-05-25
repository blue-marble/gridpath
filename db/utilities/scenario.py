#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create or update scenario.
"""
import warnings

from db.common_functions import spin_on_database_lock


def create_scenario(io, c, column_values_dict):
    """
    Flexible way to insert a scenario that does not require specifying
    values for all columns. Columns can be skipped entirely or None can be
    specified as their value (in which case this function will insert a NULL
    value for that column). The scenario_id column is auto increment, so
    should not be inserted directly. If the scenario_id is specified,
    it will be skipped (not inserted) and a warning will be raised.

    :param io: the database connection object
    :param c: database cursor object
    :param column_values_dict: dictionary containing the scenarios table
        column names to populate as keys and the scenarios table column
        values as the dictionary values
    :return: None
    """
    column_names_sql_string = str()
    column_values_sql_string = str()
    column_values_data = tuple()

    # TODO: add a check that the column names are correct and values are
    #  integers
    for column_name in column_values_dict.keys():
        if column_name == 'scenario_id':
            warnings.warn(
                "The scenario_id is an AUTOINCREMENT column and should not be "
                "inserted directly. \n"
                "Your scenario will be assigned a scenario_id automatically.\n"
                "Remove the 'scenario_id' key from the dictionary to avoid "
                "seeing this warning again.")
        else:
            if list(column_values_dict.keys()).index(column_name) == 0:
                column_names_sql_string += "{}, ".format(column_name)
                column_values_sql_string += "?,"
                column_values_data = (column_values_dict[column_name],)
            elif list(column_values_dict.keys()).index(column_name) \
                    == len(list(column_values_dict.keys())) - 1:
                column_names_sql_string += "{}".format(column_name)
                column_values_sql_string += "?"
                column_values_data = \
                    column_values_data + (column_values_dict[column_name],)
            else:
                column_names_sql_string += "{}, ".format(column_name)
                column_values_sql_string += "?,"
                column_values_data = \
                    column_values_data + (column_values_dict[column_name],)

    sql = """
        INSERT OR IGNORE INTO scenarios ({}) VALUES ({});
        """.format(column_names_sql_string, column_values_sql_string)

    spin_on_database_lock(conn=io, cursor=c, sql=sql, data=column_values_data,
                          many=False)


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
    # If no value specified, update to NULL
    if column_value is None:
        column_value = 'NULL'

    # Update the column value for the scenario
    update_sql = """
        UPDATE scenarios
        SET {} = ?
        WHERE scenario_name = ?;
        """.format(column_name)

    spin_on_database_lock(conn=io, cursor=c, sql=update_sql,
                          data=(column_value, scenario_name),
                          many=False)


def delete_scenario(conn, scenario_id):
    """
    :param conn: the database connection object
    :param scenario_id: the scenario_id to delete

    Delete a scenario fully, i.e. delete from all results tables, status
    tables, and the scenarios table.
    """
    # Delete results and statuses
    delete_scenario_results_and_status(conn=conn, scenario_id=scenario_id)

    # Delete from scenarios table
    c = conn.cursor()
    sc_id_sql = "DELETE FROM scenarios WHERE scenario_id = ?"
    spin_on_database_lock(conn=conn, cursor=c, sql=sc_id_sql,
                          data=(scenario_id,),
                          many=False)


def delete_scenario_results_and_status(conn, scenario_id):
    """
    :param conn:
    :param scenario_id:
    :return:

    Delete scenario results and statuses from relevant tables.
    """
    c = conn.cursor()
    all_tables = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()

    results_tables = [
        tbl[0] for tbl in all_tables if tbl[0].startswith("results")
    ]
    status_tables = [
        tbl[0] for tbl in all_tables if tbl[0].startswith("status")
    ]

    # Delete from all results and status tables
    for tbl in results_tables + status_tables:
        sql = """
            DELETE FROM {} WHERE scenario_id = ?;
            """.format(tbl)
        spin_on_database_lock(conn=conn, cursor=c, sql=sql,
                              data=(scenario_id,), many=False)

    # Update statuses in scenarios table to defaults
    status_sql = """
        UPDATE scenarios
        SET validation_status_id=0,
        queue_order_id=NULL,
        run_status_id=0, 
        run_process_id=NULL
        WHERE scenario_id = ?
    """
    spin_on_database_lock(conn=conn, cursor=c, sql=status_sql,
                          data=(scenario_id,), many=False)


def delete_scenario_results(conn, scenario_id):
    """
    :param conn:
    :param scenario_id:
    :return:

    Delete scenario from all results tables.
    """
    c = conn.cursor()
    all_tables = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()

    results_tables = [
        tbl[0] for tbl in all_tables if tbl[0].startswith("results")
    ]

    # Delete from all results tables
    for tbl in results_tables:
        sql = """
            DELETE FROM {} WHERE scenario_id = ?;
            """.format(tbl)
        spin_on_database_lock(conn=conn, cursor=c, sql=sql,
                              data=(scenario_id,), many=False)

