#!/usr/bin/env python

"""
Operations of variable generators. Can't provide reserves.
No curtailment variable by individual generator.
"""

import os

from pyomo.environ import *

from modules.operations.services import operational_type_set_init


def add_model_components(m):
    """

    :param m:
    :return:
    """

    m.cap_factor = Param(m.VARIABLE_GENERATORS, m.TIMEPOINTS,
                         within=PercentFraction)

    # Operations
    def max_available_power_rule(mod, g, tmp):
        return mod.capacity[g] * mod.cap_factor[g, tmp]

    m.Variable_Max_Power_in_Timepoint = Expression(m.VARIABLE_GENERATORS,
                                                   m.TIMEPOINTS,
                                                   rule=
                                                   max_available_power_rule)

    def min_power_provision_rule(mod, g, tmp):
        return mod.capacity[g] * mod.cap_factor[g, tmp]

    m.Variable_Min_Power_in_Timepoint = Expression(m.VARIABLE_GENERATORS,
                                                   m.TIMEPOINTS,
                                                   rule=
                                                   min_power_provision_rule)

    def max_headroom_rule(mod, g, tmp):
        """
        Components can include upward reserves, regulation
        :param m:
        :param g:
        :param tmp:
        :return:
        """
        if len(mod.headroom_variables[g]) > 0:
            raise ValueError(
                ("\n" +
                 "Variable generators cannot provide headroom services. "
                 + "\n" +
                 "In generators.tab, change the following flags " +
                 "for generator '{}' to 0:" + "\n" + "{}")
                .format(g, mod.headroom_variables[g])
                             )
        else:
            return mod.Provide_Headroom[g, tmp] == 0
    m.Variable_Max_Headroom_Constraint = Constraint(m.VARIABLE_GENERATORS,
                                                    m.TIMEPOINTS,
                                                    rule=max_headroom_rule)

    def max_footroom_rule(mod, g, tmp):
        """
        Components can include upward reserves, regulation
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if len(mod.footroom_variables[g]) > 0:
            raise ValueError(
                ("\n" +
                 "Variable generators cannot provide footroom services."
                 + "\n" +
                 "In generators.tab, change the following flags " +
                 "for generator '{}' to 0:" + "\n" + "{}").
                format(g, mod.footroom_variables[g])
                             )
        else:
            return mod.Provide_Footroom[g, tmp] == 0

    m.Variable_Max_Footroom_Constraint = Constraint(m.VARIABLE_GENERATORS,
                                                    m.TIMEPOINTS,
                                                    rule=max_footroom_rule)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory,
                                           "variable_generator_profiles.tab"),
                     index=(m.VARIABLE_GENERATORS, m.TIMEPOINTS),
                     param=m.cap_factor
                     )


def export_results(m):
    for g in getattr(m, "VARIABLE_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Variable_Max_Power_in_Timepoint[" + str(g) + ", "
                  + str(tmp) + "]: "
                  + str(m.Variable_Max_Power_in_Timepoint[g, tmp].expr)
                  )
            print("Variable_Min_Power_in_Timepoint[" + str(g) + ", "
                  + str(tmp) + "]: "
                  + str(m.Variable_Min_Power_in_Timepoint[g, tmp].expr)
                  )
