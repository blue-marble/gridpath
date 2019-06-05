#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import os.path
from pyomo.environ import Param, Set, NonNegativeReals


def generic_add_model_components(
        m,
        d,
        reserve_zone_set,
        reserve_zone_timepoint_set,
        reserve_requirement_param
):
    """
    Generic treatment of reserves. This function creates model components
    related to a particular reserve requirement, including
    1) the 2-dimensional set of reserve zones and timepoints for the
    requirement
    2) the reserve requirement (currently by zone and timepoint)
    :param m:
    :param d:
    :param reserve_zone_set:
    :param reserve_zone_timepoint_set:
    :param reserve_requirement_param:
    :return:
    """

    # BA-timepoint combinations with requirement
    setattr(m, reserve_zone_timepoint_set,
            Set(dimen=2,
                within=getattr(m, reserve_zone_set) * m.TIMEPOINTS
                )
            )

    # Magnitude of the requirement by reserve zone and timepoint
    setattr(m, reserve_requirement_param,
            Param(getattr(m, reserve_zone_timepoint_set),
                  within=NonNegativeReals)
            )


def generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            requirement_filename,
                            reserve_zone_timepoint_set,
                            reserve_requirement_param):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param requirement_filename:
    :param reserve_zone_timepoint_set:
    :param reserve_requirement_param:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs",
                                           requirement_filename),
                     index=getattr(m, reserve_zone_timepoint_set),
                     param=getattr(m, reserve_requirement_param)
                     )
