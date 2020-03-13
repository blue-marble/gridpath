#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import absolute_import

from pyomo.environ import Set, Expression

from .reserve_aggregation import generic_add_model_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "frequency_response_ba",
        "FREQUENCY_RESPONSE_BA_TIMEPOINTS",
        "FREQUENCY_RESPONSE_PROJECTS",
        "Provide_Frequency_Response_MW",
        "Total_Frequency_Response_Provision_MW"
        )

    m.FREQUENCY_RESPONSE_PARTIAL_PROJECTS_OPERATIONAL_IN_TIMEPOINT = \
        Set(m.TMPS,
            initialize=lambda mod, tmp:
            mod.FREQUENCY_RESPONSE_PARTIAL_PROJECTS &
                mod.OPERATIONAL_PROJECTS_IN_TIMEPOINT[tmp])

    # Reserve provision
    def total_partial_frequency_response_rule(mod, ba, tmp):
        return \
            sum(mod.Provide_Frequency_Response_MW[g, tmp]
                for g in
                mod.
                FREQUENCY_RESPONSE_PARTIAL_PROJECTS_OPERATIONAL_IN_TIMEPOINT[
                    tmp]
                if mod.frequency_response_ba[g] == ba
                   )
    m.Total_Partial_Frequency_Response_Provision_MW = \
        Expression(m.FREQUENCY_RESPONSE_BA_TIMEPOINTS,
                   rule=total_partial_frequency_response_rule)

