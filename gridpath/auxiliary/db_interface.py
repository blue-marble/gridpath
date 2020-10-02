from db.common_functions import spin_on_database_lock


def get_required_capacity_types_from_database(conn, scenario_id):
    """
    Get the required type modules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    generator capacity types in the scenario's portfolio.

    :param conn: database connection
    :param scenario_id: int, user-specified scenario ID
    :return: List of the required type modules
    """
    c = conn.cursor()

    project_portfolio_scenario_id = c.execute(
        """SELECT project_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    required_capacity_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT capacity_type 
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = ?""",
            (project_portfolio_scenario_id, )
        ).fetchall()
    ]

    return required_capacity_type_modules


# TODO: handle non-existing scenarios/scenario_ids
def get_scenario_id_and_name(scenario_id_arg, scenario_name_arg, c, script):
    """
    Get the scenario_id and the scenario_ name. Usually only one is given (the
    other one will be 'None'), so this functions determine the missing one from
    the one that is provided. If both are provided, this function checks
    whether they match.

    :param scenario_id_arg:
    :param scenario_name_arg:
    :param c:
    :param script:
    :return: (scenario_id, scenario_name)
    """

    if scenario_id_arg is None and scenario_name_arg is None:
        raise TypeError(
            """ERROR: Either scenario_id or scenario_name must be specified. 
            Run 'python """ + script + """'.py --help' for help."""
        )

    elif scenario_id_arg is not None and scenario_name_arg is None:
        result = c.execute(
            """SELECT scenario_name
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id_arg)
        ).fetchone()
        if result is None:
            raise ValueError(
                """ERROR: No matching scenario found for scenario_id '{}'"""
                .format(scenario_id_arg)
            )
        else:
            return scenario_id_arg, result[0]

    elif scenario_id_arg is None and scenario_name_arg is not None:
        result = c.execute(
            """SELECT scenario_id
               FROM scenarios
               WHERE scenario_name = '{}';""".format(scenario_name_arg)
        ).fetchone()
        if result is None:
            raise ValueError(
                """ERROR: No matching scenario found for scenario_name '{}'"""
                .format(scenario_name_arg)
            )
        else:
            return result[0], scenario_name_arg

    else:
        # If both scenario_id and scenario_name are specified
        result = c.execute(
            """SELECT scenario_name
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id_arg)
        ).fetchone()
        if result is None:
            raise ValueError(
                """ERROR: No matching scenario found for scenario_id '{}'"""
                .format(scenario_id_arg)
            )
        elif result[0] != scenario_name_arg:
            raise ValueError(
                """ERROR: scenario_id and scenario_name don't match in 
                database."""
            )
        else:
            return scenario_id_arg, scenario_name_arg


def setup_results_import(conn, cursor, table, scenario_id, subproblem, stage):
    """
    :param conn: the connection object
    :param cursor: the cursor object
    :param table: the results table we'll be inserting into
    :param scenario_id:
    :param subproblem:
    :param stage:

    Prepare for results import: 1) delete prior results and 2) create a
    temporary table we'll insert into first (for sorting before inserting
    into the final table)
    """
    # Delete prior results
    del_sql = """
        DELETE FROM {} 
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(table)
    spin_on_database_lock(conn=conn, cursor=cursor, sql=del_sql,
                          data=(scenario_id, subproblem, stage), many=False)

    # Create temporary table, which we'll use to sort the results before
    # inserting them into our persistent table
    drop_tbl_sql = \
        """DROP TABLE IF EXISTS temp_{}{};
        """.format(table, scenario_id)
    spin_on_database_lock(conn=conn, cursor=cursor, sql=drop_tbl_sql,
                          data=(), many=False)

    # Get the CREATE statemnt for the persistent table
    tbl_sql = cursor.execute("""
        SELECT sql 
        FROM sqlite_master
        WHERE type='table'
        AND name='{}'
        """.format(table)
                             ).fetchone()[0]

    # Create a temporary table with the same structure as the persistent table
    temp_tbl_sql = \
        tbl_sql.replace(
            "CREATE TABLE {}".format(table),
            "CREATE TEMPORARY TABLE temp_{}{}".format(table, scenario_id)
        )

    spin_on_database_lock(conn=conn, cursor=cursor, sql=temp_tbl_sql,
                          data=(), many=False)
