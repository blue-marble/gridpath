#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make load zones
"""
from __future__ import print_function



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
    c.execute(
        """INSERT INTO subscenarios_geography_load_zones
           (load_zone_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            load_zone_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    for zone in zones:
        c.execute(
            """INSERT INTO inputs_geography_load_zones
            (load_zone_scenario_id, load_zone,
            overgeneration_penalty_per_mw, unserved_energy_penalty_per_mw)
            VALUES ({}, '{}', {}, {});""".format(
                load_zone_scenario_id, zone, zone_overgen_penalties[zone],
                zone_unserved_energy_penalties[zone]
            )
        )
    io.commit()


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
    c.execute(
        """INSERT INTO subscenarios_geography_lf_reserves_up_bas
           (lf_reserves_up_ba_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            reserve_ba_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    for ba in bas:
        c.execute(
            """INSERT INTO inputs_geography_lf_reserves_up_bas
            (lf_reserves_up_ba_scenario_id, lf_reserves_up_ba,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES ({}, '{}', {}, {});""".format(
                reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]
            )
        )
        io.commit()
        

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
    c.execute(
        """INSERT INTO subscenarios_geography_lf_reserves_down_bas
           (lf_reserves_down_ba_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            reserve_ba_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    for ba in bas:
        c.execute(
            """INSERT INTO inputs_geography_lf_reserves_down_bas
            (lf_reserves_down_ba_scenario_id, lf_reserves_down_ba,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES ({}, '{}', {}, {});""".format(
                reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]
            )
        )
        io.commit()


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
    c.execute(
        """INSERT INTO subscenarios_geography_regulation_up_bas
           (regulation_up_ba_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            reserve_ba_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    for ba in bas:
        c.execute(
            """INSERT INTO inputs_geography_regulation_up_bas
            (regulation_up_ba_scenario_id, regulation_up_ba,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES ({}, '{}', {}, {});""".format(
                reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]
            )
        )
        io.commit()


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
    c.execute(
        """INSERT INTO subscenarios_geography_regulation_down_bas
           (regulation_down_ba_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            reserve_ba_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    for ba in bas:
        c.execute(
            """INSERT INTO inputs_geography_regulation_down_bas
            (regulation_down_ba_scenario_id, regulation_down_ba,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES ({}, '{}', {}, {});""".format(
                reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]
            )
        )
        io.commit()


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
    c.execute(
        """INSERT INTO subscenarios_geography_spinning_reserves_bas
           (spinning_reserves_ba_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            reserve_ba_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    for ba in bas:
        c.execute(
            """INSERT INTO inputs_geography_spinning_reserves_bas
            (spinning_reserves_ba_scenario_id, spinning_reserves_ba,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES ({}, '{}', {}, {});""".format(
                reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]
            )
        )
        io.commit()
        

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
    c.execute(
        """INSERT INTO subscenarios_geography_frequency_response_bas
           (frequency_response_ba_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            reserve_ba_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    for ba in bas:
        c.execute(
            """INSERT INTO inputs_geography_frequency_response_bas
            (frequency_response_ba_scenario_id, frequency_response_ba,
            violation_penalty_per_mw, reserve_to_energy_adjustment)
            VALUES ({}, '{}', {}, {});""".format(
                reserve_ba_scenario_id, ba, ba_penalties[ba],
                reserve_to_energy_adjustments[ba]
            )
        )
    io.commit()


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
    c.execute(
        """INSERT INTO subscenarios_geography_rps_zones
           (rps_zone_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            rps_zone_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # RPS zones
    for zone in zones:
        c.execute(
            """INSERT INTO inputs_geography_rps_zones
            (rps_zone_scenario_id, rps_zone)
            VALUES ({}, '{}');""".format(
                rps_zone_scenario_id, zone
            )
        )
    io.commit()
    

def geography_carbon_cap_zones(
        io, c,
        carbon_cap_zone_scenario_id,
        scenario_name,
        scenario_description,
        zones
):
    """
    Carbon cap zones
    :return:
    """
    print("carbon cap zones")

    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_geography_carbon_cap_zones
           (carbon_cap_zone_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            carbon_cap_zone_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # RPS zones
    for zone in zones:
        c.execute(
            """INSERT INTO inputs_geography_carbon_cap_zones
            (carbon_cap_zone_scenario_id, carbon_cap_zone)
            VALUES ({}, '{}');""".format(
                carbon_cap_zone_scenario_id, zone
            )
        )
    io.commit()


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
    c.execute(
        """INSERT INTO subscenarios_geography_prm_zones
           (prm_zone_scenario_id, name, description)
           VALUES ({}, '{}', '{}');""".format(
            prm_zone_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # RPS zones
    for zone in zones:
        c.execute(
            """INSERT INTO inputs_geography_prm_zones
            (prm_zone_scenario_id, prm_zone)
            VALUES ({}, '{}');""".format(
                prm_zone_scenario_id, zone
            )
        )
    io.commit()


if __name__ == "__main__":
    pass
