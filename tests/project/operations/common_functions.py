#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from collections import OrderedDict
import os.path
import pandas as pd


TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")


def get_project_operational_timepoints(project_list):
    """
    :return: a list of (prj, operational_timepoint) tuples given a list of
        projects
    """
    # Get project operational periods first
    eg_df = \
        pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs",
                "existing_generation_period_params.tab"
            ),
            usecols=['project', 'period'],
            sep="\t"
        )

    eg = [tuple(x) for x in eg_df.values if x[0] in project_list]

    ng_df = \
        pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs",
                "new_build_generator_vintage_costs.tab"
            ),
            usecols=['project', 'vintage'],
            sep="\t"
        )
    ng = [tuple(x) for x in ng_df.values if x[0] in project_list]

    es_df = \
        pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs",
                "storage_specified_capacities.tab"
            ),
            usecols=['project', 'period'],
            sep="\t"
        )
    es = [tuple(x) for x in es_df.values if x[0] in project_list]

    ns_df = \
        pd.read_csv(
            os.path.join(
                TEST_DATA_DIRECTORY, "inputs",
                "new_build_storage_vintage_costs.tab"
            ),
            usecols=['project', 'vintage'],
            sep="\t"
        )
    ns = [tuple(x) for x in ns_df.values if x[0] in project_list]

    # Manually add shiftable DR, which is available in all periods
    dr = \
        [("Shift_DR", 2020), ("Shift_DR", 2030)] \
        if "Shift_DR" in project_list \
        else []

    expected_proj_period_set = sorted(eg + ng + es + ns + dr)

    # Then get the operational periods by project
    op_per_by_proj_dict = dict()
    for proj_per in expected_proj_period_set:
        if proj_per[0] not in op_per_by_proj_dict.keys():
            op_per_by_proj_dict[proj_per[0]] = [proj_per[1]]
        else:
            op_per_by_proj_dict[proj_per[0]].append(proj_per[1])

    expected_operational_periods_by_project = OrderedDict(
        sorted(
            op_per_by_proj_dict.items()
        )
    )

    # Get the list of project-timepoint tuples for all projects
    project_operational_timepoints = list()

    timepoints_df = \
        pd.read_csv(
            os.path.join(TEST_DATA_DIRECTORY, "inputs", "timepoints.tab"),
            sep="\t", usecols=['TIMEPOINTS', 'period']
        )
    expected_tmp_in_p = dict()
    for tmp in timepoints_df.values:
        if tmp[1] not in expected_tmp_in_p.keys():
            expected_tmp_in_p[tmp[1]] = [tmp[0]]
        else:
            expected_tmp_in_p[tmp[1]].append(tmp[0])

    for proj in expected_operational_periods_by_project:
        for period in expected_operational_periods_by_project[proj]:
            for tmp in expected_tmp_in_p[period]:
                project_operational_timepoints.append(
                    (proj, tmp)
                )

    return project_operational_timepoints
