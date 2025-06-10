# Copyright 2016-2025 Blue Marble Analytics LLC.
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
from pyomo.environ import Param, Reals, Set, Expression


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
    m.f_intercept = Param(m.FOUTPUT_PROJECT_POLICY_ZONES, within=Reals, default=0)

    def zero_intercept_with_zero_capacity_rule(mod, prj, policy, zone, prd):
        if prd not in mod.OPR_PRDS_BY_PRJ[prj]:
            return 0
        else:
            return mod.f_intercept[prj, policy, zone] * mod.Capacity_MW[prj, prd]

    m.F_Intercept_Expression = Expression(
        m.FOUTPUT_PROJECT_POLICY_ZONES,
        m.PERIODS,
        initialize=zero_intercept_with_zero_capacity_rule,
    )


# Compliance type methods
def contribution_in_timepoint(mod, prj, policy, zone, tmp):
    """ """
    return (
        mod.f_slope[prj, policy, zone] * mod.Bulk_Power_Provision_MW[prj, tmp]
        + mod.F_Intercept_Expression[prj, policy, zone, mod.period[tmp]]
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
            if row[3] == "f_output":
                project_subset.append((row[0], row[1], row[2]))
                f_slope_dict[(row[0], row[1], row[2])] = float(row[4])
                f_intercept_dict[(row[0], row[1], row[2])] = float(row[5])

    data_portal.data()["FOUTPUT_PROJECT_POLICY_ZONES"] = {None: project_subset}
    data_portal.data()["f_slope"] = f_slope_dict
    data_portal.data()["f_intercept"] = f_intercept_dict
