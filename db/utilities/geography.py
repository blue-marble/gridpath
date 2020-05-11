#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make load zones
"""

from db.common_functions import spin_on_database_lock


def geography_load_zones(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    Load zones and associated params
    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_load_zones
           (load_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Inputs
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_load_zones
        (load_zone_scenario_id, load_zone,
        allow_overgeneration, overgeneration_penalty_per_mw, 
        allow_unserved_energy, unserved_energy_penalty_per_mw)
        VALUES (?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def geography_reserve_bas(
    conn, subscenario_data, inputs_data, reserve_type
):
    """

    :param conn:
    :param subscenario_data:
    :param inputs_data:
    :param reserve_type:
    """

    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_{}_bas
           ({}_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """.format(reserve_type, reserve_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Inputs
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_{}_bas
            ({}_ba_scenario_id, {}_ba, allow_violation,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES (?, ?, ?, ?, ?);
        """.format(reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


# TODO: consolidate policy and reliability functions
def geography_rps_zones(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    RPS zones and associated params.
    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_rps_zones
           (rps_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # RPS zones
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_rps_zones
        (rps_zone_scenario_id, rps_zone, allow_violation, 
        violation_penalty_per_mwh)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
    

def geography_carbon_cap_zones(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    Carbon cap zones and associated params.
    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_carbon_cap_zones
           (carbon_cap_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # RPS zones
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_carbon_cap_zones
        (carbon_cap_zone_scenario_id, carbon_cap_zone, allow_violation, 
        violation_penalty_per_emission)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def geography_prm_zones(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    PRM zones and associated params.
    """

    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_prm_zones
           (prm_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # PRM zones
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_prm_zones
        (prm_zone_scenario_id, prm_zone, allow_violation, 
        violation_penalty_per_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def geography_local_capacity_zones(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    Local capacity zones and associated params.
    """

    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_local_capacity_zones
           (local_capacity_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Local capacity zones
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_local_capacity_zones
        (local_capacity_zone_scenario_id, local_capacity_zone, 
        allow_violation, violation_penalty_per_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


if __name__ == "__main__":
    pass
