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

import csv
import os.path
from pyomo.environ import value


def fix_variables(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    Don't allow market participation if the final participation stage was before the
    current stage
    """
    if m.first_stage_flag:  # buy/sell variables not fixed in the first stage
        pass
    else:
        for z, hub, tmp in m.LZ_MARKETS * m.TMPS:
            if m.no_market_participation_in_stage[z, hub]:
                m.Net_Market_Purchased_Power[z, hub, tmp] = 0
                m.Net_Market_Purchased_Power[z, hub, tmp].fixed = True


def write_pass_through_file_headers(pass_through_directory):
    with open(
        os.path.join(pass_through_directory, "market_positions.tab"),
        "w",
        newline="",
    ) as market_positions_file:
        writer = csv.writer(market_positions_file, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "load_zone",
                "market",
                "timepoint",
                "stage",
                "final_net_market_purchased_power",
            ]
        )


def export_pass_through_inputs(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
):
    """
    This function exports the market position for all load zones and markets. This
    becomes the starting position for the following stage (for load balance purposes).

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :return:
    """

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            "pass_through_inputs",
            "market_positions.tab",
        ),
        "a",
    ) as market_positions_file:
        fixed_commitment_writer = csv.writer(
            market_positions_file, delimiter="\t", lineterminator="\n"
        )
        for lz, hub, tmp in m.LZ_MARKETS * m.TMPS:
            fixed_commitment_writer.writerow(
                [
                    lz,
                    hub,
                    tmp,
                    stage,
                    value(m.Final_Net_Market_Purchased_Power[lz, hub, tmp]),
                ]
            )
