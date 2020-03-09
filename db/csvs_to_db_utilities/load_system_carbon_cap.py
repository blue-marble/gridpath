#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load system carbon cap targets data from csvs
"""

from db.utilities import carbon_cap

def load_system_carbon_cap_targets(io, c, subscenario_input, data_input):
    """
    System carbon_cap dictionary
    {carbon_cap_zone: {period: {subproblem: {stage_id: carbon_cap_mmt}}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['carbon_cap_target_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['carbon_cap_target_scenario_id'] == sc_id)]

        zone_period_targets = dict()
        for z in data_input_subscenario['carbon_cap_zone'].unique():
            zone_period_targets[z] = dict()
            zone_period_targets_by_zone = data_input_subscenario.loc[data_input_subscenario['carbon_cap_zone'] == z]
            for p in zone_period_targets_by_zone['period'].unique():
                p = int(p)
                zone_period_targets[z][p] = dict()
                zone_period_targets_by_zone_period = zone_period_targets_by_zone.loc[
                    zone_period_targets_by_zone['period'] == p]
                for sub_id in zone_period_targets_by_zone_period['subproblem_id'].unique():
                    sub_id = int(sub_id)
                    zone_period_targets[z][p][sub_id] = dict()
                    zone_period_targets_by_zone_period_subproblem = zone_period_targets_by_zone_period.loc[
                        zone_period_targets_by_zone_period['subproblem_id'] == sub_id]
                    for st_id in zone_period_targets_by_zone_period_subproblem['stage_id'].unique():
                        st_id = int(st_id)
                        zone_period_targets[z][p][sub_id][st_id] = dict()
                        zone_period_targets[z][p][sub_id][st_id] = float(zone_period_targets_by_zone_period_subproblem.loc[
                            zone_period_targets_by_zone_period_subproblem['stage_id'] == st_id, 'carbon_cap_mmt'].iloc[0])

        # Load data into GridPath database
        carbon_cap.insert_carbon_cap_targets(
            io=io, c=c,
            carbon_cap_target_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            zone_period_targets=zone_period_targets
        )
