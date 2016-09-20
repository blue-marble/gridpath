#!/usr/bin/env python

"""
Operations of variable generators. Can be curtailed (dispatched down).
Can't provide reserves.
"""

import os.path

from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals

from modules.operations.generation_and_storage.auxiliary import generator_subset_init, \
    make_gen_tmp_var_df


def add_module_specific_components(m, scenario_directory):
    """
    Variable generators require a capacity factor for each timepoint.
    :param m:
    :return:
    """

    m.VARIABLE_GENERATORS = Set(within=m.GENERATORS,
                                initialize=generator_subset_init(
                                    "operational_type", "variable")
                                )

    m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.VARIABLE_GENERATORS))

    # TODO: allow cap factors greater than 1?
    m.cap_factor = Param(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                         within=NonNegativeReals)

    # Curtailment is a dispatch decision
    m.Curtail_MW = Var(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                       within=NonNegativeReals)

    # Can't curtail more than available power
    def curtailment_limit_rule(mod, g, tmp):
        """
        Can't curtail more than available power
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Curtail_MW[g, tmp] \
            <= mod.Capacity_MW[g, mod.period[tmp]] * mod.cap_factor[g, tmp]
    m.Curtailment_Limit_Constraint = \
        Constraint(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=curtailment_limit_rule)


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

    return mod.Capacity_MW[g, mod.period[tmp]] * mod.cap_factor[g, tmp] \
        - mod.Curtail_MW[g, tmp]


def max_power_rule(mod, g, tmp):
    """
    No variables to constrain for variable generators.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return Constraint.Skip


def min_power_rule(mod, g, tmp):
    """
    No variables to constrain for variable generators.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return Constraint.Skip


def curtailment_rule(mod, g, tmp):
    """
    Variable generation can be dispatched down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Curtail_MW[g, tmp]


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


def export_module_specific_results(mod):
    """

    :param mod:
    :return:
    """
    curtailment_df = \
        make_gen_tmp_var_df(
            mod,
            "VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Curtail_MW",
            "curtail_mw")

    mod.module_specific_df.append(curtailment_df)
