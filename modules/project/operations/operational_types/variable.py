#!/usr/bin/env python

"""
Operations of variable generators. Can be curtailed (dispatched down).
Can't provide reserves.
"""

import os.path

from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    Expression

from modules.auxiliary.auxiliary import generator_subset_init, \
    make_project_time_var_df
from modules.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables, reserve_variable_derate_params


def add_module_specific_components(m, d):
    """
    Variable generators require a capacity factor for each timepoint.
    :param m:
    :return:
    """
    # Sets and params
    m.VARIABLE_GENERATORS = Set(within=m.PROJECTS,
                                initialize=generator_subset_init(
                                    "operational_type", "variable")
                                )

    m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.VARIABLE_GENERATORS))

    # TODO: allow cap factors greater than 1?
    m.cap_factor = Param(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                         within=NonNegativeReals)

    # Variable generators treated as dispatchable (can also be curtailed and
    # provide reserves)
    m.Provide_Variable_Power_MW = \
        Var(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    def max_power_rule(mod, g, tmp):
        """
        Power provision plus upward services cannot exceed available power.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Variable_Power_MW[g, tmp] + \
            sum(
            getattr(mod, c)[g, tmp]
            / getattr(
                mod, getattr(d, reserve_variable_derate_params)[c]
            )[g]
            for c in getattr(d, headroom_variables)[g]
        ) \
            <= mod.Capacity_MW[g, mod.period[tmp]] * mod.cap_factor[g, tmp]
    m.Variable_Max_Power_Constraint = \
        Constraint(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=max_power_rule)

    def min_power_rule(mod, g, tmp):
        """
        Power provision minus downward services cannot be less than 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Variable_Power_MW[g, tmp] - \
            sum(
            getattr(mod, c)[g, tmp]
            / getattr(
                mod, getattr(d, reserve_variable_derate_params)[c]
            )[g]
            for c in getattr(d, footroom_variables)[g]
        ) \
            >= 0
    m.Variable_Min_Power_Constraint = \
        Constraint(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=min_power_rule)

    def curtailment_expression_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] * mod.cap_factor[g, tmp] - \
            mod.Provide_Variable_Power_MW[g, tmp]
    m.Variable_Generator_Curtailment_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=curtailment_expression_rule)


# Operations
def power_provision_rule(mod, g, tmp):
    """
    Power provision from variable generators is their capacity times the
    capacity factor in each timepoint minus any curtailment.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    return mod.Provide_Variable_Power_MW[g, tmp]


def curtailment_rule(mod, g, tmp):
    """
    Variable generation can be dispatched down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Variable_Generator_Curtailment_MW[g, tmp]


def fuel_cost_rule(mod, g, tmp):
    """
    Variable generators should not have fuel use
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise (ValueError(
        "ERROR! Variable generators should not use fuel." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its fuel to '.' (no value).")
    )


def startup_rule(mod, g, tmp):
    """
    Variable generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Variable generators should not incur startup costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup costs to '.' (no value).")
    )


def shutdown_rule(mod, g, tmp):
    """
    Variable generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Variable generators should not incur shutdown costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its shutdown costs to '.' (no value).")
    )


def load_module_specific_data(mod, data_portal, scenario_directory,
                              horizon, stage):
    """
    Capacity factors vary by horizon and stage, so get inputs from appropriate
    directory
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs",
                                           "variable_generator_profiles.tab"),
                     index=(mod.VARIABLE_GENERATORS, mod.TIMEPOINTS),
                     param=mod.cap_factor
                     )


def export_module_specific_results(mod, d):
    """

    :param mod:
    :param d:
    :return:
    """
    curtailment_df = \
        make_project_time_var_df(
            mod,
            "VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Variable_Generator_Curtailment_MW",
            ["project", "timepoint"],
            "curtail_mw"
        )

    d.module_specific_df.append(curtailment_df)
