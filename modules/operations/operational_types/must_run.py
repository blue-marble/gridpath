#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

import os

from pyomo.environ import *

from modules.operations.services import operational_type_set_init


def add_model_components(m):
    """

    :param m:
    :return:
    """

    def max_available_power_rule(mod, g, tmp):
        return mod.capacity[g]
    m.Must_Run_Max_Power_in_Timepoint = Expression(m.MUST_RUN_GENERATORS,
                                                   m.TIMEPOINTS,
                                                   rule=max_available_power_rule
                                                   )

    def min_power_provision_rule(mod, g, tmp):
        return mod.capacity[g]

    m.Must_Run_Min_Power_in_Timepoint = Expression(m.MUST_RUN_GENERATORS,
                                                   m.TIMEPOINTS,
                                                   rule=min_power_provision_rule
                                                   )

    def max_headroom_rule(mod, g, tmp):
        """
        Must-run generators cannot provide headroom. If flagged to provide such
        services, raise an error; otherwise, set headroom to 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if len(mod.headroom_variables[g]) > 0:
            raise ValueError(
                ("\n" +
                 "Must-run generators cannot provide headroom services. "
                 + "\n" +
                 "In generators.tab, change the following flags " +
                 "for generator '{}' to 0:" + "\n" + "{}")
                .format(g, mod.headroom_variables[g])
                             )
        else:
            return mod.Provide_Headroom[g, tmp] == 0
    m.Must_Run_Max_Headroom_Constraint = Constraint(m.MUST_RUN_GENERATORS,
                                                    m.TIMEPOINTS,
                                                    rule=max_headroom_rule)

    def max_footroom_rule(mod, g, tmp):
        """
        Must-run generators cannot provide footroom. If flagged to provide such
        services, raise an error; otherwise, set footroom to 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if len(mod.footroom_variables[g]) > 0:
            raise ValueError(
                ("\n" +
                 "Must-run generators cannot provide footroom services."
                 + "\n" +
                 "In generators.tab, change the following flags " +
                 "for generator '{}' to 0:" + "\n" + "{}").
                format(g, mod.footroom_variables[g])
                             )
        else:
            return mod.Provide_Footroom[g, tmp] == 0

    m.Max_Footroom_Must_Run_Constraint = Constraint(m.MUST_RUN_GENERATORS,
                                                    m.TIMEPOINTS,
                                                    rule=max_footroom_rule)


def export_results(m):
    for g in getattr(m, "MUST_RUN_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Must_Run_Max_Power_in_Timepoint[" + str(g) + ", "
                  + str(tmp) + "]: "
                  + str(m.Must_Run_Max_Power_in_Timepoint[g, tmp].expr)
                  )
            print("Must_Run_Min_Power_in_Timepoint[" + str(g) + ", "
                  + str(tmp) + "]: "
                  + str(m.Must_Run_Min_Power_in_Timepoint[g, tmp].expr)
                  )
