#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.


from db.common_functions import spin_on_database_lock


# TODO: subscenario-table combinations should be a data config
def generic_insert_subscenario(
    conn, subscenario, table, subscenario_data, inputs_data
):
    c = conn.cursor()

    # Subscenario
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_{}
        ({}, name, description)
        VALUES (?, ?, ?);
        """.format(table, subscenario)
    print(subs_sql)
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    # Get column names for this table
    table_data_query = c.execute(
      """SELECT * FROM inputs_{};""".format(table)
    )

    column_names = [s[0] for s in table_data_query.description]

    column_string = ", ".join(column_names)
    values_string = ", ".join(["?"] * len(column_names))

    inputs_sql = """
        INSERT OR IGNORE INTO inputs_{} ({}) VALUES ({});
        """.format(table, column_string, values_string)
    print(inputs_sql)
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
