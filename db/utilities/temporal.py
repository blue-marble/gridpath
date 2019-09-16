#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make temporal subscenarios
"""
from __future__ import print_function


def temporal(
        io, c,
        temporal_scenario_id, subproblem_id, stage_id, stage_name,
        scenario_name,
        scenario_description,
        periods, horizons, hours, number_of_hours_in_timepoint, month_dict,
        boundary, discount_factors_and_years_represented,
        timepoint_weights
):
    """

    :param io:
    :param c:
    :param temporal_scenario_id:
    :param subproblem_id:
    :param stage_id:
    :param stage_name:
    :param scenario_name:
    :param scenario_description:
    :param periods:
    :param horizons:
    :param hours:
    :param number_of_hours_in_timepoint:
    :param month_dict: {tmp: month} dictionary
    :param boundary:
    :param discount_factors_and_years_represented:
    :param timepoint_weights:
    :return:
    """

    print("timepoints")

    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_temporal
        (temporal_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            temporal_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Subproblems
    c.execute(
        """INSERT INTO inputs_temporal_subproblems
        (temporal_scenario_id, subproblem_id)
        VALUES ({}, {});""".format(
            temporal_scenario_id, subproblem_id
        )
    )
    io.commit()

    # Stages
    c.execute(
        """INSERT INTO inputs_temporal_subproblems_stages
        (temporal_scenario_id, subproblem_id, stage_id, stage_name)
        VALUES ({}, {}, {}, '{}')""".format(
            temporal_scenario_id, subproblem_id, stage_id, stage_name
        )
    )

    # Timepoints
    # Timepoint_id = period * 10^4 + horizon * 10^2 + hour
    # Horizon_id = period * 10^2 + horizon
    # TODO: timepoint ID calculation needs to be more flexible
    # TODO: CHANGE UTILITY TO NEW HORIOZON TREATMENT
    for period in periods:
        for horizon in horizons:
            for hour in hours:
                c.execute(
                    """INSERT INTO inputs_temporal_timepoints
                    (temporal_scenario_id, subproblem_id, stage_id, timepoint,
                    period, timepoint_weight, number_of_hours_in_timepoint, 
                    month)
                    VALUES ({}, {}, {},  {}, {}, {}, {});""".format(
                        temporal_scenario_id, subproblem_id, stage_id,
                        (period * 10**4 + horizon * 10**2 + hour),
                        timepoint_weights,
                        number_of_hours_in_timepoint,
                        month_dict[period * 10**4 + horizon * 10**2 + hour]
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
                (temporal_scenario_id, subproblem_id, horizon, period, 
                boundary)
                VALUES ({}, {}, {}, {}, '{}', {});""".format(
                    temporal_scenario_id, subproblem_id, horizon_id, period,
                    boundary
                )
            )
    io.commit()


if __name__ == "__main__":
    pass
