# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import OrderedDict
import os.path
import pandas as pd


TEST_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "test_data")


def get_project_operational_periods(project_list):
    """
    :return: a list of (prj, operational_timepoint) tuples given a list of
        projects
    """
    # Get project operational periods first
    eg_df = pd.read_csv(
        os.path.join(TEST_DATA_DIRECTORY, "inputs", "spec_capacity_period_params.tab"),
        usecols=["project", "period"],
        sep="\t",
    )

    eg = [tuple(x) for x in eg_df.values if x[0] in project_list]

    ng_df = pd.read_csv(
        os.path.join(
            TEST_DATA_DIRECTORY, "inputs", "new_build_generator_vintage_costs.tab"
        ),
        usecols=["project", "vintage"],
        sep="\t",
    )
    ng = [tuple(x) for x in ng_df.values if x[0] in project_list]

    ngb_df = pd.read_csv(
        os.path.join(
            TEST_DATA_DIRECTORY,
            "inputs",
            "new_binary_build_generator_vintage_costs.tab",
        ),
        usecols=["project", "vintage"],
        sep="\t",
    )
    ngb = [tuple(x) for x in ngb_df.values if x[0] in project_list]

    ns_df = pd.read_csv(
        os.path.join(
            TEST_DATA_DIRECTORY, "inputs", "new_build_storage_vintage_costs.tab"
        ),
        usecols=["project", "vintage"],
        sep="\t",
    )
    ns = [tuple(x) for x in ns_df.values if x[0] in project_list]

    nsb_df = pd.read_csv(
        os.path.join(
            TEST_DATA_DIRECTORY, "inputs", "new_binary_build_storage_vintage_costs.tab"
        ),
        usecols=["project", "vintage"],
        sep="\t",
    )
    nsb = [tuple(x) for x in nsb_df.values if x[0] in project_list]

    fp_df = pd.read_csv(
        os.path.join(TEST_DATA_DIRECTORY, "inputs", "fuel_prod_new_vintage_costs.tab"),
        usecols=["project", "vintage"],
        sep="\t",
    )
    fp_df = [tuple(x) for x in fp_df.values if x[0] in project_list]

    # Manually add shiftable DR, which is available in all periods
    dr = [("Shift_DR", 2020), ("Shift_DR", 2030)] if "Shift_DR" in project_list else []

    expected_proj_period_set = sorted(eg + ng + ngb + ns + nsb + fp_df + dr)

    return expected_proj_period_set


def get_project_operational_timepoints(project_list):
    """
    :return: a list of (prj, operational_timepoint) tuples given a list of
        projects
    """
    expected_proj_period_set = get_project_operational_periods(
        project_list=project_list
    )

    # Get the operational periods by project
    op_per_by_proj_dict = dict()
    for proj_per in expected_proj_period_set:
        if proj_per[0] not in op_per_by_proj_dict.keys():
            op_per_by_proj_dict[proj_per[0]] = [proj_per[1]]
        else:
            op_per_by_proj_dict[proj_per[0]].append(proj_per[1])

    expected_operational_periods_by_project = OrderedDict(
        sorted(op_per_by_proj_dict.items())
    )

    # Get the list of project-timepoint tuples for all projects
    project_operational_timepoints = list()

    timepoints_df = pd.read_csv(
        os.path.join(TEST_DATA_DIRECTORY, "inputs", "timepoints.tab"),
        sep="\t",
        usecols=["timepoint", "period"],
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
                project_operational_timepoints.append((proj, tmp))

    return project_operational_timepoints
