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

"""
Simplest implementation with a MWh target
"""

import csv
import os.path
from pyomo.environ import Set, Param, NonNegativeReals, PercentFraction, \
    Expression


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.RPS_ZONE_PERIODS_WITH_RPS = Set(
        dimen=2,
        within=m.RPS_ZONES * m.PERIODS
    )

    # RPS target specified in energy terms
    m.rps_target_mwh = Param(
        m.RPS_ZONE_PERIODS_WITH_RPS,
        within=NonNegativeReals,
        default=0
    )

    # RPS target specified in 'percent of load' terms
    m.rps_target_percentage = Param(
        m.RPS_ZONE_PERIODS_WITH_RPS,
        within=PercentFraction,
        default=0
    )

    # Load zones included in RPS percentage target
    m.RPS_ZONE_LOAD_ZONES = Set(
        dimen=2,
        within=m.RPS_ZONES * m.LOAD_ZONES
    )

    def rps_target_rule(mod, rps_zone, period):
        """
        The RPS target consists of two additive components: an energy term
        and a 'percent of load x load' term, where a mapping between the RPS
        zone and the load zones whose load to consider must be specified.
        Either the energy target or the percent target can be omitted (they
        default to 0). If a mapping is not specified, the
        'percent of load x load' is 0.
        """
        # If we have a map of RPS zones to load zones, apply the percentage
        # target; if no map provided, the percentage_target is 0
        if mod.RPS_ZONE_LOAD_ZONES:
            total_period_static_load = sum(
                mod.static_load_mw[lz, tmp]
                * mod.hrs_in_tmp[tmp] * mod.tmp_weight[tmp]
                for (_rps_zone, lz) in mod.RPS_ZONE_LOAD_ZONES
                if _rps_zone == rps_zone
                for tmp in mod.TMPS if tmp in mod.TMPS_IN_PRD[period]
            )
            percentage_target = \
                mod.rps_target_percentage[rps_zone, period] \
                * total_period_static_load
        else:
            percentage_target = 0

        return mod.rps_target_mwh[rps_zone, period] + percentage_target

    m.RPS_Target = Expression(
        m.RPS_ZONE_PERIODS_WITH_RPS,
        rule=rps_target_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Load the targets
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                              "inputs", "rps_targets.tab"),
        index=m.RPS_ZONE_PERIODS_WITH_RPS,
        param=(m.rps_target_mwh, m.rps_target_percentage, )
    )

    # If we have a RPS zone to load zone map input file, load it; otherwise,
    # initialize RPS_ZONE_LOAD_ZONES as an empty list
    map_filename = os.path.join(
        scenario_directory, str(subproblem), str(stage), "inputs",
        "rps_target_load_zone_map.tab"
    )
    if os.path.exists(map_filename):
        data_portal.load(
            filename=map_filename,
            set=m.RPS_ZONE_LOAD_ZONES
        )
    else:
        data_portal.data()["RPS_ZONE_LOAD_ZONES"] = {None: []}


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage

    # Get the energy and percent targets
    c = conn.cursor()
    rps_targets = c.execute(
        """SELECT rps_zone, period, rps_target_mwh, rps_target_percentage
        FROM inputs_system_rps_targets
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        USING (period)
        JOIN
        (SELECT rps_zone
        FROM inputs_geography_rps_zones
        WHERE rps_zone_scenario_id = {}) as relevant_zones
        using (rps_zone)
        WHERE rps_target_scenario_id = {}
        AND subproblem_id = {}
        AND stage_ID = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.RPS_ZONE_SCENARIO_ID,
            subscenarios.RPS_TARGET_SCENARIO_ID,
            subproblem,
            stage
        )
    )

    # Get any RPS zone to load zone mapping for the percent target
    c2 = conn.cursor()
    lz_mapping = c2.execute(
        """SELECT rps_zone, load_zone
        FROM inputs_system_rps_target_load_zone_map
        JOIN
        (SELECT rps_zone
        FROM inputs_geography_rps_zones
        WHERE rps_zone_scenario_id = {}) as relevant_zones
        using (rps_zone)
        WHERE rps_target_scenario_id = {}
        """.format(
            subscenarios.RPS_ZONE_SCENARIO_ID,
            subscenarios.RPS_TARGET_SCENARIO_ID
        )
    )

    return rps_targets, lz_mapping


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    # TODO: warn if percentage target is specified but no mapping to load
    #  zones or vice versa
    pass
    # Validation to be added
    # rps_targets = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    rps_targets.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    rps_targets, lz_mapping = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "rps_targets.tab"), "w", newline="") as \
            rps_targets_tab_file:
        writer = csv.writer(rps_targets_tab_file,
                            delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["rps_zone", "period", "rps_target_mwh", "rps_target_percentage"]
        )

        for row in rps_targets:
            # It's OK if targets are not specified; they default to 0
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    # Write the RPS zone to load zone map file for the RPS percent target if
    # there are any mappings only
    rps_lz_map_list = [row for row in lz_mapping]
    if rps_lz_map_list:
        with open(os.path.join(scenario_directory, str(subproblem), str(stage),
                               "inputs",
                               "rps_target_load_zone_map.tab"), "w",
                  newline="") as \
                rps_lz_map_tab_file:
            writer = csv.writer(rps_lz_map_tab_file,
                                delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["rps_zone", "load_zone"]
            )
            for row in rps_lz_map_list:
                writer.writerow(row)
    else:
        pass
