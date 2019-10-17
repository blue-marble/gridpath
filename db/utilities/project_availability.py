#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project availability
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def make_scenario_and_insert_types_and_ids(
        io, c,
        project_availability_scenario_id,
        scenario_name,
        scenario_description,
        project_types_and_char_ids
):
    """

    :param io:
    :param c:
    :param project_availability_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param project_types_and_char_ids:
    :return:
    """
    print("project availability")
    # Subscenarios
    subs_data = [(project_availability_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_availability (
        project_availability_scenario_id, name,
        description) VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert all projects into project availability types table
    inputs_data = []
    for prj in list(project_types_and_char_ids.keys()):
        inputs_data.append(
            (project_availability_scenario_id,
             prj,
             project_types_and_char_ids[prj]["type"],
             project_types_and_char_ids[prj]["exogenous_availability_id"],
             project_types_and_char_ids[prj]["endogenous_availability_id"])
        )

    inputs_sql = """
        INSERT INTO inputs_project_availability_types
        (project_availability_scenario_id, project, availability_type,
        exogenous_availability_scenario_id, 
        endogenous_availability_scenario_id)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def insert_project_availability_exogenous(
        io, c, project_avail_scenarios, project_avail
):
    """
    :param io: 
    :param c:
    :param project_avail_scenarios: two-level dictionary by project and 
        subscenario id, with the subscenario name and description as a tuple 
        value
    :param project_avail: four-level dictionary with availability derate by
        project, exogenous_availability_scenario_id, stage, and timepoint
    """
    print("...exogenous")

    # "Subscenario"
    subs_data = []
    for prj in project_avail_scenarios.keys():
        for scenario_id in project_avail_scenarios[prj].keys():
            subs_data.append(
                (prj, scenario_id, 
                 project_avail_scenarios[prj][scenario_id][0],
                 project_avail_scenarios[prj][scenario_id][1])
            )
    subs_sql = """
        INSERT INTO subscenarios_project_availability_exogenous
        (project, exogenous_availability_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Inputs
    inputs_data = []
    for prj in list(project_avail.keys()):
        for subscenario_id in list(project_avail[prj].keys()):
            for stage in list(project_avail[prj][subscenario_id].keys()):
                for tmp in list(project_avail[prj][subscenario_id][stage]
                                .keys()):
                    inputs_data.append(
                        (prj, subscenario_id, stage, int(tmp),
                         project_avail[prj][subscenario_id][stage][tmp]
                         )
                    )
    inputs_sql = """
        INSERT INTO inputs_project_availability_exogenous
        (project, exogenous_availability_scenario_id, stage_id, timepoint, 
        availability_derate)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def insert_project_availability_endogenous(
        io, c, project_avail_scenarios, project_avail
):
    """
    :param io: 
    :param c:
    :param project_avail_scenarios: two-level dictionary by project and 
        subscenario id, with the subscenario name and description as a tuple 
        value
    :param project_avail: three-level dictionary with unavailable hours per
        period and per event by project,
        endogenous_availability_scenario_id; the per period param is then
        under the 'unavailable_hours_per_period' key and the per event param
        is under the 'unavailable_hours_per_event' key
    """
    print("...endogenous")

    # "Subscenario"
    subs_data = []
    for prj in project_avail_scenarios.keys():
        for scenario_id in project_avail_scenarios[prj].keys():
            subs_data.append(
                (prj, scenario_id, 
                 project_avail_scenarios[prj][scenario_id][0],
                 project_avail_scenarios[prj][scenario_id][1])
            )
    subs_sql = """
        INSERT INTO subscenarios_project_availability_endogenous
        (project, endogenous_availability_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Inputs
    inputs_data = []
    for prj in list(project_avail.keys()):
        for subscenario_id in list(project_avail[prj].keys()):
            inputs_data.append(
                (prj, subscenario_id,
                 project_avail[subscenario_id][prj[
                     "unavailable_hours_per_period"]],
                 project_avail[subscenario_id][prj[
                     "unavailable_hours_per_event"]])
            )
    inputs_sql = """
        INSERT INTO inputs_project_availability_endogenous
        (project, endogenous_availability_scenario_id, 
        unavailable_hours_per_period,
        unavailable_hours_per_event)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
