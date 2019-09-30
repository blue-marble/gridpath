#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make load zones
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def geography_load_zones(
        io, c,
        load_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones,
        zone_overgen_penalties,
        zone_unserved_energy_penalties
):
    """
    Load zones and associated params
    :return:
    """
    print("load zones")

    # Subscenarios
    subs_data = [(load_zone_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_load_zones
           (load_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for lz in zones:
        inputs_data.append((load_zone_scenario_id, lz, 
                        zone_overgen_penalties[lz],
                        zone_unserved_energy_penalties[lz]))
    inputs_sql = """
        INSERT INTO inputs_geography_load_zones
        (load_zone_scenario_id, load_zone,
        overgeneration_penalty_per_mw, unserved_energy_penalty_per_mw)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


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
    Load-following up BAs and associated params
    :return:
    """
    print("lf reserves up bas")

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_lf_reserves_up_bas
           (lf_reserves_up_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append((reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]))     
    inputs_sql = """
        INSERT INTO inputs_geography_lf_reserves_up_bas
            (lf_reserves_up_ba_scenario_id, lf_reserves_up_ba,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES (?, ?, ?, ?);
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
    Load-following down BAs and associated params
    :return:
    """
    print("lf reserves down bas")

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_lf_reserves_down_bas
           (lf_reserves_down_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba, ba_penalties[ba],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT INTO inputs_geography_lf_reserves_down_bas
        (lf_reserves_down_ba_scenario_id, lf_reserves_down_ba,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?);
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
    Regulation up BAs and associated params
    :return:
    """
    print("regulation up bas")

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_regulation_up_bas
           (regulation_up_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append((reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]))
    inputs_sql = """
        INSERT INTO inputs_geography_regulation_up_bas
        (regulation_up_ba_scenario_id, regulation_up_ba,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?);
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
    Regulation down BAs and associated params
    :return:
    """
    print("regulation down bas")

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_regulation_down_bas
           (regulation_down_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append((reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]))
    inputs_sql = """
        INSERT INTO inputs_geography_regulation_down_bas
        (regulation_down_ba_scenario_id, regulation_down_ba,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?);
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
    Spinning reserves BAs and associated params
    :return:
    """
    print("spinning reserves bas")

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_spinning_reserves_bas
           (spinning_reserves_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba, ba_penalties[ba],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT INTO inputs_geography_spinning_reserves_bas
        (spinning_reserves_ba_scenario_id, spinning_reserves_ba,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?);
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
    Frequency response BAs and associated params
    :return:
    """
    print("frequency response bas")

    # Subscenarios
    subs_data = [(reserve_ba_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_frequency_response_bas
           (frequency_response_ba_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    inputs_data = []
    for ba in bas:
        inputs_data.append(
            (reserve_ba_scenario_id, ba, ba_penalties[ba],
             reserve_to_energy_adjustments[ba])
        )
    inputs_sql = """
        INSERT INTO inputs_geography_frequency_response_bas
        (frequency_response_ba_scenario_id, frequency_response_ba,
        violation_penalty_per_mw, reserve_to_energy_adjustment)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_rps_zones(
        io, c,
        rps_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones
):
    """
    RPS zones
    :return:
    """
    print("rps zones")

    # Subscenarios
    subs_data = [(rps_zone_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_rps_zones
           (rps_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # RPS zones
    inputs_data = []
    for zone in zones:
        inputs_data.append((rps_zone_scenario_id, zone))
    inputs_sql = """
        INSERT INTO inputs_geography_rps_zones
        (rps_zone_scenario_id, rps_zone)
        VALUES (?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
    

def geography_carbon_cap_zones(
        io, c,
        carbon_cap_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones
):
    """
    Carbon cap zones
    """
    print("carbon cap zones")
    # Subscenarios
    subs_data = [(carbon_cap_zone_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_carbon_cap_zones
           (carbon_cap_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # RPS zones
    inputs_data = []
    for zone in zones:
        inputs_data.append((carbon_cap_zone_scenario_id, zone))
    inputs_sql = """
        INSERT INTO inputs_geography_carbon_cap_zones
        (carbon_cap_zone_scenario_id, carbon_cap_zone)
        VALUES (?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_prm_zones(
        io, c,
        prm_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones
):
    """
    PRM zones
    :return:
    """
    print("prm zones")

    # Subscenarios
    subs_data = [(prm_zone_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_prm_zones
           (prm_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # PRM zones
    inputs_data = []
    for zone in zones:
        inputs_data.append((prm_zone_scenario_id, zone))
    inputs_sql = """
        INSERT INTO inputs_geography_prm_zones
        (prm_zone_scenario_id, prm_zone)
        VALUES (?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def geography_local_capacity_zones(
        io, c,
        local_capacity_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones
):
    """
    PRM zones
    :return:
    """
    print("local capacity zones")

    # Subscenarios
    subs_data = [(local_capacity_zone_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_geography_local_capacity_zones
           (local_capacity_zone_scenario_id, name, description)
           VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Local capacity zones
    inputs_data = []
    for zone in zones:
        inputs_data.append((local_capacity_zone_scenario_id, zone))
    inputs_sql = """
        INSERT INTO inputs_geography_local_capacity_zones
        (local_capacity_zone_scenario_id, local_capacity_zone)
        VALUES (?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
