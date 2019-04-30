#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.


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
