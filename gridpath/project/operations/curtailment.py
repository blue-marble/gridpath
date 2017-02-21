#!/usr/bin/env python

"""
Describe operational constraints on the generation infrastructure.
"""
from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Keep track of curtailment
    def scheduled_curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the scheduled
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            scheduled_curtailment_rule(mod, g, tmp)

    # TODO: possibly create this only if needed by another module?
    m.Scheduled_Curtailment_MW = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=scheduled_curtailment_rule
    )

    def subhourly_curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            subhourly_curtailment_rule(mod, g, tmp)

    # TODO: possibly create this only if needed by another module?
    m.Subhourly_Curtailment_MW = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=subhourly_curtailment_rule
    )

    def subhourly_energy_delivered_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            subhourly_energy_delivered_rule(mod, g, tmp)

    # TODO: possibly create this only if needed by another module?
    m.Subhourly_Energy_Delivered_MW = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=subhourly_energy_delivered_rule
    )
