#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Var, Constraint, NonNegativeReals


def generic_add_model_components(
        m,
        d,
        reserve_zone_timepoint_set,
        reserve_violation_variable,
        reserve_requirement_param,
        total_reserve_provision_expression,
        meet_reserve_constraint,
):
    """
    Ensure reserves are balanced
    :param m:
    :param d:
    :param reserve_zone_timepoint_set:
    :param reserve_violation_variable:
    :param reserve_requirement_param:
    :param total_reserve_provision_expression:
    :param meet_reserve_constraint:
    :return:
    """

    # Penalty for violation
    setattr(m, reserve_violation_variable,
            Var(getattr(m, reserve_zone_timepoint_set),
                within=NonNegativeReals)
            )

    # Reserve constraints
    def meet_reserve_rule(mod, ba, tmp):
        return getattr(mod, total_reserve_provision_expression)[ba, tmp] \
            + getattr(mod, reserve_violation_variable)[ba, tmp] \
            == getattr(mod, reserve_requirement_param)[ba, tmp]

    setattr(m, meet_reserve_constraint,
            Constraint(getattr(m, reserve_zone_timepoint_set),
                       rule=meet_reserve_rule))


def generic_export_results(scenario_directory, horizon, stage, m, d,
                           filename,
                           column_name,
                           reserve_zone_timepoint_set,
                           reserve_violation_variable
                           ):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :param filename:
    :param column_name:
    :param reserve_zone_timepoint_set:
    :param reserve_violation_variable:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           filename), "wb") \
            as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["zone", "timepoint",
                         column_name]
                        )
        for (ba, tmp) in getattr(m, reserve_zone_timepoint_set):
            writer.writerow([
                ba,
                tmp,
                getattr(m, reserve_violation_variable)[ba, tmp].value]
            )


def generic_save_duals(m, reserve_constraint_name):
    """

    :param m:
    :param reserve_constraint_name:
    :return:
    """
    m.constraint_indices[reserve_constraint_name] = \
        ["zone", "timepoint", "dual"]
