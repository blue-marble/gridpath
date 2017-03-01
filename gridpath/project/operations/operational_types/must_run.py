#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of must-run generators. Can't provide reserves.
"""

from pyomo.environ import Constraint, Set

from gridpath.auxiliary.auxiliary import generator_subset_init


def add_module_specific_components(m, d):
    """

    :param m:
    :return:
    """

    m.MUST_RUN_GENERATORS = Set(within=m.PROJECTS,
                                initialize=generator_subset_init(
                                    "operational_type", "must_run")
                                )

    m.MUST_RUN_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.MUST_RUN_GENERATORS))


def power_provision_rule(mod, g, tmp):
    """
    Power provision for must run generators is their capacity.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision for must-run generators, if eligible, is their capacity.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    Can't dispatch down and curtailment not allowed
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_curtailment_rule(mod, g, tmp):
    """
    Can't provide reserves
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    Can't provide reserves
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: add data check that minimum_input_mmbtu_per_hr is 0 for must-run gens
# TODO: change when can-build-new
def fuel_burn_rule(mod, g, tmp, error_message):
    """
    Output doesn't vary, so this is a constant
    Return 0 if must-run generator with no fuel (e.g. geothermal); these
    should not have been given a fuel or labeled carbonaceous in the first
    place
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return mod.inc_heat_rate_mmbtu_per_mwh[g] \
            * mod.Power_Provision_MW[g, tmp]
    else:
        raise ValueError(error_message)


def startup_rule(mod, g, tmp):
    """
    Must-run generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Must-run generators should not incur startup costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup costs to '.' (no value).")
    )


def shutdown_rule(mod, g, tmp):
    """
    Must-run generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Must-run generators should not incur shutdown costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its shutdown costs to '.' (no value).")
    )
