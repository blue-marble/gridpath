#!/usr/bin/env python

"""
Operations of no-commit generators.
"""

from pyomo.environ import Set, Var, NonNegativeReals

from modules.operations.generation_and_storage.auxiliary import generator_subset_init


def add_module_specific_components(m, scenario_directory):
    """

    :param m:
    :param scenario_directory:
    :return:
    """

    m.DISPATCHABLE_NO_COMMIT_GENERATORS = Set(
        within=m.GENERATORS,
        initialize=
        generator_subset_init("operational_type", "dispatchable_no_commit")
    )

    m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_NO_COMMIT_GENERATORS))
    
    m.Provide_Power_DispNoCommit_MW = \
        Var(m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispNoCommit_MW[g, tmp]


def max_power_rule(mod, g, tmp):
    """
    Power plus upward services cannot exceed capacity.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispNoCommit_MW[g, tmp] + \
        mod.Headroom_Provision_MW[g, tmp] \
        <= mod.Capacity_MW[g, mod.period[tmp]]


def min_power_rule(mod, g, tmp):
    """
    Power minus downward services cannot be below 0 (no commitment variable).
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
        mod.Footroom_Provision_MW[g, tmp] \
        >= 0


def curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: add data check that minimum_input_mmbtu_per_hr is 0 for no-commit gens
def fuel_cost_rule(mod, g, tmp):
    """
    Fuel use in terms of an IO curve with an incremental heat rate above
    the minimum stable level, which is 0 for no-commit generators, so just
    multiply power by the incremental heat rate
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return (mod.Provide_Power_DispNoCommit_MW[g, tmp]
            * mod.inc_heat_rate_mmbtu_per_mwh[g]
            ) * mod.fuel_price_per_mmbtu[mod.fuel[g].value]


# TODO: what should these return -- what is the no-commit modeling?
def startup_rule(mod, g, tmp):
    """
    No commit variables, so shouldn't happen
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! No-commit generators should not incur startup costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup costs to '.' (no value).")
    )


def shutdown_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! No-commit generators should not incur shutdown costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its shutdown costs to '.' (no value).")
    )
