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

"""

"""


from pyomo.environ import Set, Var, Constraint, NonNegativeReals, Expression


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    m.CAP_TRANSFER_ZONES_BY_PRM_PRJ = Set(
        m.PRM_PROJECTS,
        within=m.PRM_ZONES,
        initialize=lambda mod, prj: [
            tz
            for (z, tz) in mod.PRM_ZONES_CAPACITY_TRANSFER_ZONES
            if z == mod.prm_zone[prj]
        ],
    )

    m.PRM_PRJ_OPR_PRDS_CAP_TRANSFER_ZONES = Set(
        dimen=3,
        within=m.PRM_PRJ_OPR_PRDS * m.PRM_ZONES,
        initialize=lambda mod: [
            (prj, prd, z)
            for (prj, prd) in mod.PRM_PRJ_OPR_PRDS
            for z in mod.CAP_TRANSFER_ZONES_BY_PRM_PRJ[prj]
        ],
    )
    # m.ELCC_Eligible_Capacity_MW = Expression(
    #     m.PRM_PRJ_OPR_PRDS, rule=elcc_eligible_capacity_rule
    # )

    m.Transfer_Capacity_Contribution = Var(
        m.PRM_PRJ_OPR_PRDS_CAP_TRANSFER_ZONES, within=NonNegativeReals
    )

    m.Keep_Capacity_Contribution = Var(m.PRM_PRJ_OPR_PRDS, within=NonNegativeReals)

    def allocation_balance_rule(mod, prj, prd):
        return (
            mod.Keep_Capacity_Contribution[prj, prd]
            + sum(
                mod.Transfer_Capacity_Contribution[prj, prd, z]
                for z in mod.CAP_TRANSFER_ZONES_BY_PRM_PRJ[prj]
            )
            <= mod.PRM_Simple_Contribution_MW[prj, prd]
        )

    m.Capacity_Allocation_Balance_Constraint = Constraint(
        m.PRM_PRJ_OPR_PRDS, rule=allocation_balance_rule
    )
