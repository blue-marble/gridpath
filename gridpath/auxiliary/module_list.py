#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from importlib import import_module
import os.path
import pandas as pd
import sys


def all_modules_list():
    # If all optional modules are selected, this would be the list
    all_modules = [
        "temporal.operations.timepoints",
        "temporal.operations.horizons",
        "temporal.investment.periods",
        "geography.load_zones",
        "geography.load_following_up_balancing_areas",
        "geography.load_following_down_balancing_areas",
        "geography.regulation_up_balancing_areas",
        "geography.regulation_down_balancing_areas",
        "geography.frequency_response_balancing_areas",
        "geography.rps_zones",
        "geography.carbon_cap_zones",
        "geography.prm_zones",
        "system.load_balance.static_load_requirement",
        "system.reserves.requirement.lf_reserves_up",
        "system.reserves.requirement.lf_reserves_down",
        "system.reserves.requirement.regulation_up",
        "system.reserves.requirement.regulation_down",
        "system.reserves.requirement.frequency_response",
        "system.policy.rps.rps_requirement",
        "system.policy.carbon_cap.carbon_cap",
        "system.prm.prm_requirement",
        "project",
        "project.capacity.capacity_types",
        "project.capacity.capacity",
        "project.capacity.costs",
        "project.fuels",
        "project.operations",
        "project.operations.reserves.lf_reserves_up",
        "project.operations.reserves.lf_reserves_down",
        "project.operations.reserves.regulation_up",
        "project.operations.reserves.regulation_down",
        "project.operations.reserves.frequency_response",
        "project.operations.operational_types",
        "project.operations.reserves.op_type_dependent.lf_reserves_up",
        "project.operations.reserves.op_type_dependent.lf_reserves_down",
        "project.operations.reserves.op_type_dependent.regulation_up",
        "project.operations.reserves.op_type_dependent.regulation_down",
        "project.operations.reserves.op_type_dependent.frequency_response",
        "project.operations.power",
        "project.operations.fix_commitment",
        "project.operations.costs",
        "project.operations.tuning_costs",
        "project.operations.recs",
        "project.operations.carbon_emissions",
        "project.operations.fuel_burn",
        "project.prm",
        "project.prm.prm_simple",
        "project.prm.elcc_surface",
        "transmission",
        "transmission.capacity.capacity_types",
        "transmission.capacity.capacity",
        "transmission.operations.operations",
        "transmission.operations.costs",
        "transmission.operations.simultaneous_flow_limits",
        "transmission.operations.carbon_emissions",
        "system.load_balance.aggregate_project_power",
        "system.load_balance.aggregate_transmission_power",
        "system.load_balance.load_balance",
        "system.reserves.aggregation.lf_reserves_up",
        "system.reserves.aggregation.regulation_up",
        "system.reserves.aggregation.lf_reserves_down",
        "system.reserves.aggregation.regulation_down",
        "system.reserves.aggregation.frequency_response",
        "system.reserves.balance.lf_reserves_up",
        "system.reserves.balance.regulation_up",
        "system.reserves.balance.lf_reserves_down",
        "system.reserves.balance.regulation_down",
        "system.reserves.balance.frequency_response",
        "system.policy.rps.aggregate_recs",
        "system.policy.rps.rps_balance",
        "system.policy.carbon_cap.aggregate_project_carbon_emissions",
        "system.policy.carbon_cap.aggregate_transmission_carbon_emissions",
        "system.policy.carbon_cap.carbon_balance",
        "system.prm.aggregate_project_simple_prm_contribution",
        "system.prm.elcc_surface",
        "system.prm.prm_balance",
        "objective.project.aggregate_capacity_costs",
        "objective.project.aggregate_operational_costs",
        "objective.project.aggregate_operational_tuning_costs",
        "objective.transmission.aggregate_operational_costs",
        "objective.transmission.carbon_imports_tuning_costs",
        "objective.system.aggregate_load_balance_penalties",
        "objective.system.reserve_violation_penalties.lf_reserves_up",
        "objective.system.reserve_violation_penalties.lf_reserves_down",
        "objective.system.reserve_violation_penalties.regulation_up",
        "objective.system.reserve_violation_penalties.regulation_down",
        "objective.system.reserve_violation_penalties.frequency_response",
        "objective.system.prm.dynamic_elcc_tuning_penalties",
        "objective.min_total_cost"
    ]
    return all_modules


def optional_modules_list():
    # Names of groups of optional modules (features as keys)
    optional_modules = {
        "fuels":
            ["project.fuels", "project.operations.fuel_burn"],
        "multi_stage":
            ["project.operations.fix_commitment"],
        "transmission":
            ["transmission",
             "transmission.capacity.capacity",
             "transmission.operations.operations",
             "system.load_balance.aggregate_transmission_power"],
        "transmission_hurdle_rates":
             ["transmission.operations.costs",
              "objective.transmission.aggregate_operational_costs"],
        "lf_reserves_up":
            ["geography.load_following_up_balancing_areas",
             "system.reserves.requirement.lf_reserves_up",
             "project.operations.reserves.lf_reserves_up",
             "project.operations.reserves.op_type_dependent.lf_reserves_up",
             "system.reserves.aggregation.lf_reserves_up",
             "system.reserves.balance.lf_reserves_up",
             "objective.system.reserve_violation_penalties.lf_reserves_up"],
        "lf_reserves_down":
            ["geography.load_following_down_balancing_areas",
             "system.reserves.requirement.lf_reserves_down",
             "project.operations.reserves.lf_reserves_down",
             "project.operations.reserves.op_type_dependent.lf_reserves_down",
             "system.reserves.aggregation.lf_reserves_down",
             "system.reserves.balance.lf_reserves_down",
             "objective.system.reserve_violation_penalties.lf_reserves_down"],
        "regulation_up":
            ["geography.regulation_up_balancing_areas",
             "system.reserves.requirement.regulation_up",
             "project.operations.reserves.regulation_up",
             "project.operations.reserves.op_type_dependent.regulation_up",
             "system.reserves.aggregation.regulation_up",
             "system.reserves.balance.regulation_up",
             "objective.system.reserve_violation_penalties.regulation_up"],
        "regulation_down":
            ["geography.regulation_down_balancing_areas",
             "system.reserves.requirement.regulation_down",
             "project.operations.reserves.regulation_down",
             "system.reserves.aggregation.regulation_down",
             "project.operations.reserves.op_type_dependent.regulation_down",
             "system.reserves.balance.regulation_down",
             "objective.system.reserve_violation_penalties.regulation_down"],
        "frequency_response":
            ["geography.frequency_response_balancing_areas",
             "system.reserves.requirement.frequency_response",
             "project.operations.reserves.frequency_response",
             "project.operations.reserves.op_type_dependent.frequency_response",
             "system.reserves.aggregation.frequency_response",
             "system.reserves.balance.frequency_response",
             "objective.system.reserve_violation_penalties.frequency_response"],
        "rps":
            ["geography.rps_zones",
             "system.policy.rps.rps_requirement",
             "project.operations.recs",
             "system.policy.rps.aggregate_recs",
             "system.policy.rps.rps_balance"],
        "carbon_cap":
            ["geography.carbon_cap_zones",
             "system.policy.carbon_cap.carbon_cap",
             "project.operations.carbon_emissions",
             "system.policy.carbon_cap.aggregate_project_carbon_emissions",
             "system.policy.carbon_cap.carbon_balance"],
        "prm":
            ["geography.prm_zones",
             "system.prm.prm_requirement",
             "project.prm",
             "project.prm.prm_simple",
             "system.prm.aggregate_project_simple_prm_contribution",
             "system.prm.prm_balance"]
    }
    return optional_modules


def cross_feature_modules_list():
    # Some modules depend on more than one supermodule
    # Currently, these are: track_carbon_imports and simultaneous_flow_limits
    cross_modules = {
        ("transmission", "carbon_cap", "track_carbon_imports"):
        ["system.policy.carbon_cap.aggregate_transmission_carbon_emissions",
         "transmission.operations.carbon_emissions",
         "objective.transmission.carbon_imports_tuning_costs"],
        ("transmission", "simultaneous_flow_limits"):
            ["transmission.operations.simultaneous_flow_limits"],
        ("prm", "elcc_surface"):
            ["project.prm.elcc_surface", "system.prm.elcc_surface",
             "objective.system.prm.dynamic_elcc_tuning_penalties"]
    }
    return cross_modules


def get_features(scenario_directory):
    """
    Modules needed for scenario
    :param scenario_directory:
    :return:
    """
    features_file = os.path.join(scenario_directory, "features.csv")
    try:
        requested_features = pd.read_csv(features_file)["features"].tolist()
    except IOError:
        print("ERROR! Features file {} not found".format(features_file))
        sys.exit(1)

    # Remove any modules not requested by user
    modules_to_use = all_modules_list()

    optional_modules = optional_modules_list()
    for feature in optional_modules.keys():
        if feature in requested_features:
            pass
        else:
            for m in optional_modules[feature]:
                modules_to_use.remove(m)

    # Some modules depend on more than one feature
    # We have to check if all features that the module depends on are
    # specified before removing it
    cross_feature_modules = cross_feature_modules_list()
    for feature_group in cross_feature_modules.keys():
        if all(feature in requested_features
               for feature in feature_group):
            pass
        else:
            for m in cross_feature_modules[feature_group]:
                modules_to_use.remove(m)

    return modules_to_use


def load_modules(modules_to_use):
    """
    Load modules, keep track of which modules have been imported
    :param modules_to_use:
    :return:
    """
    loaded_modules = list()
    for m in modules_to_use:
        try:
            imported_module = import_module("."+m, package='gridpath')
            loaded_modules.append(imported_module)
        except ImportError:
            print("ERROR! Module " + str(m) + " not found.")
            sys.exit(1)

    return loaded_modules
