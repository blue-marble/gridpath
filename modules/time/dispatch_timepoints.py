#!/usr/bin/env python
import os

from pyomo.environ import *


def add_model_components(m):
    m.TIMEPOINTS = Set(within=NonNegativeIntegers)

    # TODO: eventually make this the first timepoint of the dispatch horizon
    m.first_timepoint = Param(
        initialize=lambda mod: min(tmp for tmp in mod.TIMEPOINTS))

    m.last_timepoint = Param(
        initialize=lambda mod: max(tmp for tmp in mod.TIMEPOINTS))

    def previous_timepoint_init(mod, tmp):
        if tmp == mod.first_timepoint:
            return mod.last_timepoint
        else:
            return tmp-1

    m.previous_timepoint = Param(m.TIMEPOINTS,
                                 initialize=previous_timepoint_init)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "timepoints.tab"),
                     set=m.TIMEPOINTS
                     )
