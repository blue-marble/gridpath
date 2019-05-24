#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make temporal subscenarios
"""
from __future__ import print_function


def temporal(
        io, c,
        temporal_scenario_id, scenario_name, scenario_description,
        periods, horizons, hours, number_of_hours_in_timepoint,
        boundary, discount_factors_and_years_represented,
        horizon_weights_and_months
):
    """
    
    :param io: 
    :param c: 
    :param temporal_scenario_id:
    :param scenario_name: 
    :param scenario_description: 
    :param periods: 
    :param horizons: 
    :param hours: 
    :param number_of_hours_in_timepoint: 
    :param boundary: 
    :param discount_factors_and_years_represented: 
    :param horizon_weights_and_months: 
    :return: 
    """

    print("timepoints")

    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_temporal_timepoints
        (temporal_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            temporal_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Timepoints
    # Timepoint_id = period * 10^4 + horizon * 10^2 + hour
    # Horizon_id = period * 10^2 + horizon
    for period in periods:
        for horizon in horizons:
            for hour in hours:
                c.execute(
                    """INSERT INTO inputs_temporal_timepoints
                    (temporal_scenario_id, timepoint,
                    period, horizon, number_of_hours_in_timepoint)
                    VALUES ({}, {}, {}, {}, {});""".format(
                        temporal_scenario_id,
                        (period * 10**4 + horizon * 10**2 + hour),
                        period, period * 10**2 + horizon,
                        number_of_hours_in_timepoint
                    )
                )
    io.commit()

    print("periods")
    for period in periods:
        c.execute(
            """INSERT INTO inputs_temporal_periods
            (temporal_scenario_id, period, discount_factor,
            number_years_represented)
            VALUES ({}, {}, {}, {});""".format(
                temporal_scenario_id, period,
                discount_factors_and_years_represented[period]["df"],
                discount_factors_and_years_represented[period]["y"]
            )
        )
    io.commit()

    print("horizons")
    for period in periods:
        for horizon in horizons:
            horizon_id = period * 100 + horizon
            c.execute(
                """INSERT INTO inputs_temporal_horizons
                (temporal_scenario_id, horizon, period, boundary,
                horizon_weight, month)
                VALUES ({}, {}, {}, '{}', {}, {});""".format(
                    temporal_scenario_id, horizon_id, period, boundary,
                    horizon_weights_and_months[horizon]["weight"],
                    horizon_weights_and_months[horizon]["month"]

                )
            )
    io.commit()


if __name__ == "__main__":
    temporal(
        io=None,
        c=None,
        temporal_scenario_id=None,
        scenario_name=None,
        scenario_description=None,
        periods=None,
        horizons=None,
        hours=None,
        number_of_hours_in_timepoint=None,
        boundary=None,
        discount_factors_and_years_represented=None,
        horizon_weights_and_months=None
    )
