#!/usr/bin/env python

"""
Describes the relationships among timepoints in the optimization
"""

import os.path

from pyomo.environ import Set, Param, NonNegativeIntegers


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    m.HORIZONS = Set(within=NonNegativeIntegers, ordered=True)
    m.boundary = Param(m.HORIZONS)

    m.horizon = Param(m.TIMEPOINTS, within=m.HORIZONS)

    m.TIMEPOINTS_ON_HORIZON = \
        Set(m.HORIZONS,
            initialize=lambda mod, h:
            set(tmp for tmp in mod.TIMEPOINTS if mod.horizon[tmp] == h))

    # TODO: make more robust that relying on min and max
    m.first_horizon_timepoint = \
        Param(m.HORIZONS,
              initialize=
              lambda mod, h: min(tmp for tmp in mod.TIMEPOINTS_ON_HORIZON[h]))

    m.last_horizon_timepoint = \
        Param(m.HORIZONS,
              initialize=
              lambda mod, h: max(tmp for tmp in mod.TIMEPOINTS_ON_HORIZON[h]))

    def previous_timepoint_init(mod, tmp):
        for h in mod.HORIZONS:
            if tmp == mod.first_horizon_timepoint[h]:
                if mod.boundary[h] == "circular":
                    return mod.last_horizon_timepoint[h]
                elif mod.boundary[h] == "linear":
                    return None
                else:
                    raise ValueError(
                        "Invalid boundary value '{}' for horizon '{}'".
                        format(mod.boundary[h], h) + "\n" +
                        "Horizon boundary must be either 'circular' or 'linear'"
                    )
            else:
                return tmp-1

    m.previous_timepoint = \
        Param(m.TIMEPOINTS,
              initialize=previous_timepoint_init)


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    """
    """
    data_portal.load(filename=os.path.join(scenario_directory, horizon,
                                           "inputs", "horizons.tab"),
                     select=("HORIZONS", "boundary"),
                     index=m.HORIZONS,
                     param=(m.boundary,)
                     )

    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "timepoints.tab"),
                     select=("TIMEPOINTS","horizon"),
                     index=m.TIMEPOINTS,
                     param=m.horizon
                     )
