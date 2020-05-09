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


def geography_lf_reserves_up_bas(
        io, c,
        reserve_ba_scenario_id,
        scenario_name,
        scenario_description,
        bas,
        ba_penalties,
        reserve_to_energy_adjustments
):
    """
    :param io:
    :param c:
    :param reserve_ba_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param bas: list of BAs
    :param ba_penalties: dictionary with the BA as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the BA
    :param reserve_to_energy_adjustments:
    :return:

    Load-following up BAs and associated params
    """

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_lf_reserves_up_bas
           (lf_reserves_up_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba,
             ba_penalties[ba][0], ba_penalties[ba][1],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_lf_reserves_up_bas
            (lf_reserves_up_ba_scenario_id, lf_reserves_up_ba, allow_violation,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
        

def geography_lf_reserves_down_bas(
        io, c,
        reserve_ba_scenario_id,
        scenario_name,
        scenario_description,
        bas,
        ba_penalties,
        reserve_to_energy_adjustments
):
    """
    :param io:
    :param c:
    :param reserve_ba_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param bas: list of BAs
    :param ba_penalties: dictionary with the BA as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the BA
    :param reserve_to_energy_adjustments:
    :return:

    Load-following down BAs and associated params.
    """

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_lf_reserves_down_bas
           (lf_reserves_down_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba,
             ba_penalties[ba][0], ba_penalties[ba][1],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_lf_reserves_down_bas
        (lf_reserves_down_ba_scenario_id, lf_reserves_down_ba, allow_violation,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_regulation_up_bas(
        io, c,
        reserve_ba_scenario_id,
        scenario_name,
        scenario_description,
        bas,
        ba_penalties,
        reserve_to_energy_adjustments
):
    """
    :param io:
    :param c:
    :param reserve_ba_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param bas: list of BAs
    :param ba_penalties: dictionary with the BA as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the BA
    :param reserve_to_energy_adjustments:
    :return:

    Regulation up BAs and associated params.
    """

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_regulation_up_bas
           (regulation_up_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba,
             ba_penalties[ba][0], ba_penalties[ba][1],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_regulation_up_bas
        (regulation_up_ba_scenario_id, regulation_up_ba, allow_violation,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_regulation_down_bas(
        io, c,
        reserve_ba_scenario_id,
        scenario_name,
        scenario_description,
        bas,
        ba_penalties,
        reserve_to_energy_adjustments
):
    """
   :param io:
    :param c:
    :param reserve_ba_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param bas: list of BAs
    :param ba_penalties: dictionary with the BA as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the BA
    :param reserve_to_energy_adjustments:
    :return:

    Regulation down BAs and associated params.
    """

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_regulation_down_bas
           (regulation_down_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba,
             ba_penalties[ba][0], ba_penalties[ba][1],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_regulation_down_bas
        (regulation_down_ba_scenario_id, regulation_down_ba, allow_violation,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_spinning_reserves_bas(
        io, c,
        reserve_ba_scenario_id,
        scenario_name,
        scenario_description,
        bas,
        ba_penalties,
        reserve_to_energy_adjustments
):
    """
    :param io:
    :param c:
    :param reserve_ba_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param bas: list of BAs
    :param ba_penalties: dictionary with the BA as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the BA
    :param reserve_to_energy_adjustments:
    :return:

    Spinning reserves BAs and associated params.
    """

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_spinning_reserves_bas
           (spinning_reserves_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba,
             ba_penalties[ba][0], ba_penalties[ba][1],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_spinning_reserves_bas
        (spinning_reserves_ba_scenario_id, spinning_reserves_ba, allow_violation,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
        

def geography_frequency_response_bas(
        io, c,
        reserve_ba_scenario_id,
        scenario_name,
        scenario_description,
        bas,
        ba_penalties,
        reserve_to_energy_adjustments
):
    """
    :param io:
    :param c:
    :param reserve_ba_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param bas: list of BAs
    :param ba_penalties: dictionary with the BA as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the BA
    :param reserve_to_energy_adjustments:
    :return:

    Frequency response BAs and associated params.
    """

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_frequency_response_bas
           (frequency_response_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba,
             ba_penalties[ba][0], ba_penalties[ba][1],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_frequency_response_bas
        (frequency_response_ba_scenario_id, frequency_response_ba,
        allow_violation, violation_penalty_per_mw, 
        reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_rps_zones(
        io, c,
        rps_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones,
        zone_penalties
):
    """
    :param io:
    :param c:
    :param rps_zone_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zones: list of zones
    :param zone_penalties: dictionary with the zone as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the zone
    :return:

    RPS zones and associated params.
    """

    # Subscenarios
    subs_data = [(rps_zone_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_rps_zones
           (rps_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # RPS zones
    inputs_data = []
    for zone in zones:
        inputs_data.append(
            (rps_zone_scenario_id, zone,
             zone_penalties[zone][0], zone_penalties[zone][1])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_rps_zones
        (rps_zone_scenario_id, rps_zone, allow_violation, 
        violation_penalty_per_mwh)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
    

def geography_carbon_cap_zones(
        io, c,
        carbon_cap_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones,
        zone_penalties
):
    """
    :param io:
    :param c:
    :param carbon_cap_zone_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zones: list of zones
    :param zone_penalties: dictionary with the zone as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the zone
    :return:

    Carbon cap zones and associated params.
    """
    # Subscenarios
    subs_data = [(carbon_cap_zone_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_carbon_cap_zones
           (carbon_cap_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # RPS zones
    inputs_data = []
    for zone in zones:
        inputs_data.append(
            (carbon_cap_zone_scenario_id, zone,
             zone_penalties[zone][0], zone_penalties[zone][1])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_carbon_cap_zones
        (carbon_cap_zone_scenario_id, carbon_cap_zone, allow_violation, 
        violation_penalty_per_emission)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_prm_zones(
        io, c,
        prm_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones,
        zone_penalties
):
    """
    :param io:
    :param c:
    :param prm_zone_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zones: list of zones
    :param zone_penalties: dictionary with the zone as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the zone
    :return:

    PRM zones and associated params.
    """

    # Subscenarios
    subs_data = [(prm_zone_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_prm_zones
           (prm_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # PRM zones
    inputs_data = []
    for zone in zones:
        inputs_data.append(
            (prm_zone_scenario_id, zone,
             zone_penalties[zone][0], zone_penalties[zone][1])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_prm_zones
        (prm_zone_scenario_id, prm_zone, allow_violation, 
        violation_penalty_per_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_local_capacity_zones(
        io, c,
        local_capacity_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones,
        zone_penalties
):
    """
    :param io:
    :param c:
    :param local_capacity_zone_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zones: list of zones
    :param zone_penalties: dictionary with the zone as key and a
        tuple containing a boolean for whether violation is allowed and the
        violation penalty for the zone
    :return:

    Local capacity zones and associated params.
    """

    # Subscenarios
    subs_data = [(local_capacity_zone_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_geography_local_capacity_zones
           (local_capacity_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Local capacity zones
    inputs_data = []
    for zone in zones:
        inputs_data.append(
            (local_capacity_zone_scenario_id, zone,
             zone_penalties[zone][0], zone_penalties[zone][1])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_geography_local_capacity_zones
        (local_capacity_zone_scenario_id, local_capacity_zone, 
        allow_violation, violation_penalty_per_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
