# Copyright 2016-2024 Blue Marble Analytics LLC.
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

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Reals, Set


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """ """
    m.FOUTPUT_PROJECT_POLICY_ZONES = Set(dimen=3, within=m.PROJECT_POLICY_ZONES)
    m.f_slope = Param(m.FOUTPUT_PROJECT_POLICY_ZONES, within=Reals, default=0)
    m.f_intercept = Param(m.PROJECT_POLICY_ZONES, within=Reals, default=0)


# Compliance type methods
# TODO: deal with f_intercept, make sure it's zero when capacity is zero;
#  needs constraint limiting to less than capacity
def contribution_in_timepoint(mod, prj, policy, zone, tmp):
    """ """
    if mod.capacity_type[prj] == "gen_spec":
        f_intercept = (
            mod.f_intercept[prj, policy, zone]
            if mod.gen_spec_capacity_mw[prj, mod.period[tmp]] > 0
            else 0
        )
    else:
        f_intercept = mod.f_intercept[prj, policy, zone]
    return (
        mod.f_slope[prj, policy, zone] * mod.Bulk_Power_Provision_MW[prj, tmp]
        + f_intercept
    )


# IO
def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    project_subset = list()

    dynamic_components = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "project_policy_zones.tab",
        ),
        sep="\t",
        usecols=["project", "policy_name", "policy_zone", "compliance_type"],
    )

    for row in zip(
        dynamic_components["project"],
        dynamic_components["policy_name"],
        dynamic_components["policy_zone"],
        dynamic_components["compliance_type"],
    ):
        if row[3] == "f_output":
            project_subset.append((row[0], row[1], row[2]))

    data_portal.data()["FOUTPUT_PROJECT_POLICY_ZONES"] = {None: project_subset}

    f_slope_dict = {}
    f_intercept_dict = {}

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "project_policy_zones.tab",
        ),
        "r",
    ) as f:
        reader = csv.reader(f, delimiter="\t", lineterminator="\n")
        next(reader)

        for row in reader:
            if (row[0], row[1], row[2]) in project_subset:
                f_slope_dict[(row[0], row[1], row[2])] = float(row[4])
                f_intercept_dict[(row[0], row[1], row[2])] = float(row[5])

    data_portal.data()["f_slope"] = f_slope_dict
    data_portal.data()["f_intercept"] = f_intercept_dict
