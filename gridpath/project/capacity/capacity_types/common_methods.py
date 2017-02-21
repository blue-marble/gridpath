#!/usr/bin/env python


# TODO: if vintage is 2020 and lifetime is 30, is the project available in
# 2050 or not -- maybe have options for how this should be treated?
def operational_periods_by_project_vintage(periods, vintage, lifetime):
    """
    Get a list of operational periods by vintage depending on lifetime
    :param periods:
    :param vintage:
    :param lifetime:
    :return:
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
    Get the periods in which each project COULD be operational
    :param project_vintages_set:
    :param operational_periods_by_project_vintage_set:
    :return:
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
    Get the project vintages that COULD be operational in each period
    :param project_vintage_set:
    :param operational_periods_by_project_vintage_set:
    :param period:
    :return:
    """
    project_vintages = list()
    for (prj, v) in project_vintage_set:
        if period in operational_periods_by_project_vintage_set[prj, v]:
            project_vintages.append((prj, v))
        else:
            pass
    return project_vintages
