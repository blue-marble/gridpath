#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import os.path
from pyomo.environ import Param, Set, NonNegativeReals, PercentFraction, \
    Expression


def generic_add_model_components(
    m,
    d,
    reserve_zone_set,
    reserve_zone_timepoint_set,
    reserve_requirement_tmp_param,
    reserve_requirement_percentage_param,
    reserve_zone_load_zone_set,
    reserve_requirement_expression
):
    """
    Generic treatment of reserves. This function creates model components
    related to a particular reserve requirement, including
    1) the 2-dimensional set of reserve zones and timepoints for the
    requirement
    2) the reserve requirement (currently by zone and timepoint)
    :param m:
    :param d:
    :param reserve_zone_set:
    :param reserve_zone_timepoint_set:
    :param reserve_requirement_tmp_param:
    :param reserve_requirement_percentage_param:
    :param reserve_zone_load_zone_set:
    :param reserve_requirement_expression:
    :return:
    """

    # BA-timepoint combinations with requirement
    setattr(m, reserve_zone_timepoint_set,
            Set(dimen=2,
                within=getattr(m, reserve_zone_set) * m.TMPS
                )
            )

    # Magnitude of the requirement by reserve zone and timepoint
    setattr(m, reserve_requirement_tmp_param,
            Param(getattr(m, reserve_zone_timepoint_set),
                  within=NonNegativeReals,
                  default=0)
            )

    # Requirement as percentage of load
    setattr(m, reserve_requirement_percentage_param,
            Param(getattr(m, reserve_zone_set),
                  within=PercentFraction,
                  default=0)
            )

    # Load zones included in the reserve percentage requirement
    setattr(m, reserve_zone_load_zone_set,
            Set(dimen=2,
                within=getattr(m, reserve_zone_set) * m.LOAD_ZONES
                )
            )

    def reserve_requirement_rule(mod, reserve_zone, tmp):
        # If we have a map of reserve zones to load zones, apply the percentage
        # target; if no map provided, the percentage_target is 0
        if getattr(mod, reserve_zone_load_zone_set):
            percentage_target = sum(
                getattr(mod, reserve_requirement_percentage_param)[
                    reserve_zone, tmp
                ] * mod.static_load_mw[lz, tmp]
                for (_reserve_zone, lz)
                in getattr(mod, reserve_zone_load_zone_set)
                if _reserve_zone == reserve_zone
            )
        else:
            percentage_target = 0

        return \
            getattr(mod, reserve_requirement_tmp_param)[reserve_zone, tmp] \
            + percentage_target

    # TODO: apply to all reserve zone timepoints; previously we could skip
    #  some timepoints, so figure out how to deal with that
    setattr(m, reserve_requirement_expression,
            Expression(getattr(m, reserve_zone_set) * m.TMPS,
                       rule=reserve_requirement_rule)
            )


def generic_load_model_data(m, d, data_portal,
                            scenario_directory, subproblem, stage,
                            requirement_filename,
                            reserve_zone_timepoint_set,
                            reserve_requirement_param):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param requirement_filename:
    :param reserve_zone_timepoint_set:
    :param reserve_requirement_param:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                                           "inputs",
                                           requirement_filename),
                     index=getattr(m, reserve_zone_timepoint_set),
                     param=getattr(m, reserve_requirement_param)
                     )


def generic_get_inputs_from_database(
    subscenarios, subproblem, stage, conn, reserve_type,
    reserve_type_ba_subscenario_id, reserve_type_req_subscenario_id
):
    """
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :param reserve_type:
    :param reserve_type_ba_subscenario_id:
    :param reserve_type_req_subscenario_id:
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()

    tmp_req = c.execute(
        """SELECT {}_ba, timepoint, {}_mw
        FROM inputs_system_{}
        INNER JOIN
        (SELECT timepoint
        FROM inputs_temporal_timepoints
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}) as relevant_timepoints
        USING (timepoint)
        INNER JOIN
        (SELECT {}_ba
        FROM inputs_geography_{}_bas
        WHERE {}_ba_scenario_id = {}) as relevant_bas
        USING ({}_ba)
        WHERE {}_scenario_id = {}
        AND stage_id = {}
        """.format(
            reserve_type,
            reserve_type,
            reserve_type,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            reserve_type,
            reserve_type,
            reserve_type,
            reserve_type_ba_subscenario_id,
            reserve_type,
            reserve_type,
            reserve_type_req_subscenario_id,
            stage
        )
    )

    c2 = conn.cursor()
    # Get any percentage requirement
    percentage_req = c2.execute("""
        SELECT {}_ba, percent_load_req
        FROM inputs_system_{}_percentage
        WHERE {}_scenario_id = {}
        """.format(
        reserve_type,
        reserve_type,
        reserve_type,
        reserve_type_req_subscenario_id
    )
    )

    # Get any reserve zone to load zone mapping for the percent target
    c3 = conn.cursor()
    lz_mapping = c3.execute(
        """SELECT {}_ba, load_zone
        FROM inputs_system_{}_percentage_lz_map
        JOIN
        (SELECT {}_ba
        FROM inputs_geography_{}_bas
        WHERE {}_ba_scenario_id = {}) as relevant_bas
        USING ({}_ba)
        WHERE {}_scenario_id = {}
        """.format(
            reserve_type,
            reserve_type,
            reserve_type,
            reserve_type,
            reserve_type,
            reserve_type_ba_subscenario_id,
            reserve_type,
            reserve_type,
            reserve_type_req_subscenario_id
        )
    )

    return tmp_req, percentage_req, lz_mapping
