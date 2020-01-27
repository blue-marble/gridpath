#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path

from db.common_functions import spin_on_database_lock

# TODO: if vintage is 2020 and lifetime is 30, is the project available in
#  2050 or not -- maybe have options for how this should be treated?
def operational_periods_by_project_vintage(periods, vintage, lifetime):
    """
    :param periods: the study periods
    :param vintage: the project vintage
    :param lifetime: the project-vintage lifetime
    :return: the operational periods given the study periods and
        the project vintage and lifetime

    Given the list of study periods and the project's vintage and lifetime,
    this function returns the list of periods that a project with
    this vintage and lifetime will be operational.
    """
    operational_periods = list()
    for p in periods:
        if vintage <= p < vintage + lifetime:
            operational_periods.append(p)
        else:
            pass
    return operational_periods


def project_operational_periods(project_vintages_set,
                                operational_periods_by_project_vintage_set):
    """
    :param project_vintages_set: the possible project-vintages when capacity
        can be built
    :param operational_periods_by_project_vintage_set: the project operational
        periods based on vintage
    :return: all study periods when the project could be operational

    Get the periods in which each project COULD be operational given all
    project-vintages and operational periods by project-vintage (the
    lifetime is allowed to differ by vintage).
    """
    return set((g, p)
               for (g, v) in project_vintages_set
               for p
               in operational_periods_by_project_vintage_set[g, v]
               )


def project_vintages_operational_in_period(
        project_vintage_set, operational_periods_by_project_vintage_set,
        period):
    """
    :param project_vintage_set: possible project-vintages when capacity
        could be built
    :param operational_periods_by_project_vintage_set: the periods when
        project capacity of a particular vintage could be operational
    :param period: the period we're in
    :return: all vintages that could be operational in a period

    Get the project vintages that COULD be operational in each period.
    """
    project_vintages = list()
    for (prj, v) in project_vintage_set:
        if period in operational_periods_by_project_vintage_set[prj, v]:
            project_vintages.append((prj, v))
        else:
            pass
    return project_vintages


def update_capacity_results_table(
     db, c, results_directory, scenario_id, subproblem, stage, results_file
):
    results = []
    with open(os.path.join(results_directory, results_file), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        header = next(reader)

        for row in reader:
            project = row[0]
            period = row[1]
            new_build_mw = get_header_value(header, "new_build_mw")
            new_build_mwh = get_header_value(header, "new_build_mwh")
            new_build_binary = get_header_value(header, "new_build_binary")
            retired_mw = get_header_value(header, "retired_mw")
            retired_binary = get_header_value(header, "retired_binary")

            results.append(
                (new_build_mw, new_build_mwh, new_build_binary,
                 retired_mw, retired_binary,
                 scenario_id, project, period, subproblem, stage)
            )

    # Update the results table with the module-specific results
    update_sql = """
        UPDATE results_project_capacity
        SET new_build_mw = ?,
        new_build_mwh = ?,
        new_build_binary = ?,
        retired_mw = ?,
        retired_binary = ?
        WHERE scenario_id = ?
        AND project = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """

    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=results)


def get_header_value(header, column):
    """

    :param header:
    :param column:
    :return:
    """
    try:
        column_value = header.index(column)
    except ValueError:
        column_value = None

    return column_value
