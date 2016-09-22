#!/usr/bin/env python

import csv
import os.path
from pyomo.environ import Set

from reserve_requirements import add_generic_reserve_components


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # TODO: flexible, as requirement does not have to be specified for all
    # timepoints, but has memory implications
    m.LF_RESERVE_UP_ZONE_TIMEPOINTS = Set(dimen=2)
    m.LF_RESERVE_UP_ZONES = \
        Set(initialize=
            lambda mod: set(i[0] for i in mod.LF_RESERVE_UP_ZONE_TIMEPOINTS)
            )

    add_generic_reserve_components(
        m,
        d,
        reserve_zone_param="lf_reserves_up_zone",
        reserve_zone_timepoint_set="LF_RESERVE_UP_ZONE_TIMEPOINTS",
        reserve_violation_variable="LF_Reserves_Up_Violation_MW",
        reserve_violation_penalty_param=
        "lf_reserves_up_violation_penalty_per_mw",
        reserve_requirement_param="lf_reserves_up_requirement_mw",
        reserve_generator_set="LF_RESERVES_UP_RESOURCES",
        generator_reserve_provision_variable="Provide_LF_Reserves_Up_MW",
        total_reserve_provision_expression="Total_LF_Reserves_Up_Provision_MW",
        meet_reserve_constraint="Meet_LF_Reserves_Up_Constraint",
        objective_function_reserve_penalty_cost_component=
        "LF_Reserve_Up_Penalty_Costs"
        )


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs",
                                           "lf_reserves_up_requirement.tab"),
                     index=m.LF_RESERVE_UP_ZONE_TIMEPOINTS,
                     param=m.lf_reserves_up_requirement_mw
                     )


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "lf_reserves_up_violation.csv"), "wb") \
            as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["zone", "timepoint",
                         "lf_reserves_up_violation_mw"]
                        )
        for (z, tmp) in getattr(m, "LF_RESERVE_DOWN_ZONE_TIMEPOINTS"):
            writer.writerow([
                z,
                tmp,
                m.LF_Reserves_Up_Violation_MW[z, tmp].value]
            )


def save_duals(m):
    m.constraint_indices["Meet_LF_Reserves_Up_Constraint"] = \
        ["zone", "timepoint", "dual"]
