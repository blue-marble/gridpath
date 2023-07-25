# Copyright 2016-2020 Blue Marble Analytics LLC.
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

from pyomo.environ import Param, NonNegativeReals, PercentFraction


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """ """
    # Derived params to use downstream instead of always having to keep track
    # for the objective function

    m.period_objective_coefficient = Param(
        m.PERIODS,
        within=NonNegativeReals,
        initialize=lambda mod, prd: mod.discount_factor[prd]
        * mod.number_years_represented[prd],
    )

    m.tmp_objective_coefficient = Param(
        m.TMPS,
        within=NonNegativeReals,
        initialize=lambda mod, tmp: mod.discount_factor[mod.period[tmp]]
        * mod.number_years_represented[mod.period[tmp]]
        * mod.tmp_weight[tmp]
        * mod.hrs_in_tmp[tmp],
    )

    # Only used in post-processing duals for now as no costs are incurred at
    # the horizon level; weighted sum the coefficients of the periods the
    # horizon spans; if in a single period, simply use the period coefficient
    # WARNING: thread carefully, this is difficult to interpret if periods
    # have a vastly different number of years for example
    m.fraction_of_horizon_in_period = Param(
        m.BLN_TYPE_HRZS,
        m.PERIODS,
        within=PercentFraction,
        default=0,
        initialize=lambda mod, bt, h, prd: (
            sum(
                mod.hrs_in_tmp[tmp] * mod.tmp_weight[tmp]
                for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, h]
                if mod.period[tmp] == prd
            )
        )
        / sum(
            mod.hrs_in_tmp[tmp] * mod.tmp_weight[tmp]
            for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, h]
        ),
    )

    m.hrz_objective_coefficient = Param(
        m.BLN_TYPE_HRZS,
        within=NonNegativeReals,
        initialize=lambda mod, bt, h: sum(
            mod.period_objective_coefficient[prd]
            * mod.fraction_of_horizon_in_period[bt, h, prd]
            for prd in mod.PERIODS
        ),
    )
