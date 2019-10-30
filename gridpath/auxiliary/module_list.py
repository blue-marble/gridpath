#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module contains:

1) the list of all GridPath modules;
2) the modules included in each optional feature;
3) the 'cross-feature' modules;
4) the method for determining the user-requested features for the scenarios;
5) the method for loading modules.
"""

from __future__ import print_function

from builtins import str
from importlib import import_module
import os.path
import pandas as pd
import sys


def all_modules_list():
    """
    :return: list of all GridPath modules in order they are loaded

    This is the list of all GridPath modules in the order they would be
    loaded if all optional features were selected.

    Note: technically speaking some modules listed below are "packages", i.e.
    they are a collection of Python modules. For example,  "project" is a
    directory that contains both modules (project.fuels) and other sub-packages
    (project.capacity.capacity_types, project.operations, etc.). A package must
    contain an additional __init__.py file to distinguish a package from a
    directory that just happens to contain a bunch of Python scripts. In some
    cases, these __init__.py files will contain code and functions as well which
    can be accessed by importing the respective package.
    When Python imports a package, it will return a Python module object.
    """
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
        "geography.spinning_reserves_balancing_areas",
        "geography.rps_zones",
        "geography.carbon_cap_zones",
        "geography.prm_zones",
        "geography.local_capacity_zones",
        "system.load_balance.static_load_requirement",
        "system.reserves.requirement.lf_reserves_up",
        "system.reserves.requirement.lf_reserves_down",
        "system.reserves.requirement.regulation_up",
        "system.reserves.requirement.regulation_down",
        "system.reserves.requirement.frequency_response",
        "system.reserves.requirement.spinning_reserves",
        "system.policy.rps.rps_requirement",
        "system.policy.carbon_cap.carbon_cap",
        "system.reliability.prm.prm_requirement",
        "system.reliability.local_capacity.local_capacity_requirement",
        "project",
        "project.capacity.capacity_types",
        "project.capacity.capacity",
        "project.capacity.costs",
        "project.availability.availability",
        "project.fuels",
        "project.operations",
        "project.operations.reserves.lf_reserves_up",
        "project.operations.reserves.lf_reserves_down",
        "project.operations.reserves.regulation_up",
        "project.operations.reserves.regulation_down",
        "project.operations.reserves.frequency_response",
        "project.operations.reserves.spinning_reserves",
        "project.operations.operational_types",
        "project.operations.reserves.op_type_dependent.lf_reserves_up",
        "project.operations.reserves.op_type_dependent.lf_reserves_down",
        "project.operations.reserves.op_type_dependent.regulation_up",
        "project.operations.reserves.op_type_dependent.regulation_down",
        "project.operations.reserves.op_type_dependent.frequency_response",
        "project.operations.reserves.op_type_dependent.spinning_reserves",
        "project.operations.power",
        "project.operations.fix_commitment",
        "project.operations.fuel_burn",
        "project.operations.costs",
        "project.operations.tuning_costs",
        "project.operations.recs",
        "project.operations.carbon_emissions",
        "project.reliability.prm",
        "project.reliability.prm.prm_types",
        "project.reliability.prm.prm_simple",
        "project.reliability.prm.elcc_surface",
        "project.reliability.prm.group_costs",
        "project.reliability.local_capacity",
        "project.reliability.local_capacity.local_capacity_contribution",
        "transmission",
        "transmission.capacity.capacity_types",
        "transmission.capacity.capacity",
        "transmission.operations.operational_types",
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
        "system.reserves.aggregation.spinning_reserves",
        "system.reserves.balance.lf_reserves_up",
        "system.reserves.balance.regulation_up",
        "system.reserves.balance.lf_reserves_down",
        "system.reserves.balance.regulation_down",
        "system.reserves.balance.frequency_response",
        "system.reserves.balance.spinning_reserves",
        "system.policy.rps.aggregate_recs",
        "system.policy.rps.rps_balance",
        "system.policy.carbon_cap.aggregate_project_carbon_emissions",
        "system.policy.carbon_cap.aggregate_transmission_carbon_emissions",
        "system.policy.carbon_cap.carbon_balance",
        "system.reliability.prm.aggregate_project_simple_prm_contribution",
        "system.reliability.prm.elcc_surface",
        "system.reliability.prm.prm_balance",
        "system.reliability.local_capacity"
        ".aggregate_local_capacity_contribution",
        "system.reliability.local_capacity.local_capacity_balance",
        "objective.project.aggregate_capacity_costs",
        "objective.project.aggregate_prm_group_costs",
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
        "objective.system.reserve_violation_penalties.spinning_reserves",
        "objective.system.policy.aggregate_rps_violation_penalties",
        "objective.system.policy.aggregate_carbon_cap_violation_penalties",
        "objective.system.reliability.prm.dynamic_elcc_tuning_penalties",
        "objective.system.reliability.local_capacity"
        ".aggregate_local_capacity_violation_penalties",
        "objective.min_total_cost"
    ]
    return all_modules


def optional_modules_list():
    """
    :return: dictionary with the optional feature names as keys and a list
        of the modules included in each feature as values

    These are all of GridPath's optional modules grouped by features (
    features as the dictionary keys). Each of these modules belongs to only
    one feature.
    """
    optional_modules = {
        "fuels":
            ["project.fuels", "project.operations.fuel_burn"],
        "multi_stage":
            ["project.operations.fix_commitment"],
        "transmission":
            ["transmission",
             "transmission.capacity.capacity_types",
             "transmission.capacity.capacity",
             "transmission.operations.operational_types",
             "transmission.operations.operations",
             "system.load_balance.aggregate_transmission_power"],
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
             "project.operations.reserves.op_type_dependent."
             "frequency_response",
             "system.reserves.aggregation.frequency_response",
             "system.reserves.balance.frequency_response",
             "objective.system.reserve_violation_penalties.frequency_response"
             ],
        "spinning_reserves":
            ["geography.spinning_reserves_balancing_areas",
             "system.reserves.requirement.spinning_reserves",
             "project.operations.reserves.spinning_reserves",
             "project.operations.reserves.op_type_dependent.spinning_reserves",
             "system.reserves.aggregation.spinning_reserves",
             "system.reserves.balance.spinning_reserves",
             "objective.system.reserve_violation_penalties.spinning_reserves"],
        "rps":
            ["geography.rps_zones",
             "system.policy.rps.rps_requirement",
             "project.operations.recs",
             "system.policy.rps.aggregate_recs",
             "system.policy.rps.rps_balance",
             "objective.system.policy.aggregate_rps_violation_penalties"],
        "carbon_cap":
            ["geography.carbon_cap_zones",
             "system.policy.carbon_cap.carbon_cap",
             "project.operations.carbon_emissions",
             "system.policy.carbon_cap.aggregate_project_carbon_emissions",
             "system.policy.carbon_cap.carbon_balance",
             "objective.system.policy.aggregate_carbon_cap_violation_penalties"
             ],
        "prm":
            ["geography.prm_zones",
             "system.reliability.prm.prm_requirement",
             "project.reliability.prm",
             "project.reliability.prm.prm_types",
             "project.reliability.prm.prm_simple",
             "project.reliability.prm.group_costs",
             "system.reliability.prm."
             "aggregate_project_simple_prm_contribution",
             "system.reliability.prm.prm_balance",
             "objective.project."
             "aggregate_prm_group_costs",
             "objective.system.reliability.prm."
             "aggregate_prm_violation_penalties"
             ],
        "local_capacity":
            ["geography.local_capacity_zones",
             "system.reliability.local_capacity.local_capacity_requirement",
             "project.reliability.local_capacity",
             "project.reliability.local_capacity.local_capacity_contribution",
             "system.reliability.local_capacity"
             ".aggregate_local_capacity_contribution",
             "system.reliability.local_capacity.local_capacity_balance",
             "objective.system.reliability.local_capacity"
             ".aggregate_local_capacity_violation_penalties",
             ],
        "tuning": [
            "project.operations.tuning_costs",
            "objective.project.aggregate_operational_tuning_costs"
            ]
    }
    return optional_modules


def cross_feature_modules_list():
    """
    :return: dictionary with a tuple of features as keys and a list of
        modules to be included if all those features are selected as values

    Some modules depend on more than one feature, i.e. they are included
    only if multiple features are selected. These relationships are
    described in the 'cross_modules' dictionary here.
    """
    cross_modules = {
        ("transmission", "transmission_hurdle_rates"):
            ["transmission.operations.costs",
             "objective.transmission.aggregate_operational_costs"],
        ("transmission", "carbon_cap", "track_carbon_imports"):
            ["system.policy.carbon_cap"
             ".aggregate_transmission_carbon_emissions",
             "transmission.operations.carbon_emissions"],
        ("transmission", "carbon_cap", "track_carbon_imports", "tuning"):
            ["objective.transmission.carbon_imports_tuning_costs"],
        ("transmission", "simultaneous_flow_limits"):
            ["transmission.operations.simultaneous_flow_limits"],
        ("prm", "elcc_surface"):
            ["project.reliability.prm.elcc_surface",
             "system.reliability.prm.elcc_surface"],
        ("prm", "elcc_surface", "tuning"):
            ["objective.system.reliability.prm.dynamic_elcc_tuning_penalties"]
    }
    return cross_modules


def determine_modules(features=None, scenario_directory=None,):
    """
    :param features: List of requested features. Optional input; if
        not specified, function will try to load 'features.csv' file to
        determine the requested features.
    :param scenario_directory: the scenario directory, where we will look
        for the list of requested features. Optional input; if not specified,
        function will look for the 'features' input parameter
    :return: the list of modules -- a subset of all GridPath modules -- needed
        for a scenario. These are the module names, not the actual modules.

    This method determines which modules are needed for a scenario based on
    the features specified for the scenario. The features can be either
    directly specified as a list or by providing the directory where a
    'features.csv' file lists the requested features.

    We start with the list of all GridPath modules from *all_modules_list()*
    as the list of modules to use in the scenario. We then iterate over all
    optional features, which we get from the keys of the
    *optional_modules_list()* method above; if the feature is in the list of
    user-requested features, we do nothing; if it is not, we remove all of the
    feature's modules from the list of modules to use. Similarly, for the cross
    feature modules, which we get from the *cross_feature_module_list()* method,
    we check if all features they depend on are included and, if not, remove
    those modules from the list of modules to use.
    """
    if (scenario_directory is None) and (features is None):
        raise IOError("""Need to specify either 'scenario_directory', the
                      directory where 'features.csv' is saved, or 'features',
                      the list of requested features""")
    elif features is not None:
        requested_features = features
    elif scenario_directory is not None:
        features_file = os.path.join(scenario_directory, "features.csv")
        try:
            requested_features = pd.read_csv(features_file)["features"].tolist()
        except IOError:
            print("ERROR! Features file {} not found in {}.".format(
                features_file, scenario_directory
            ))
            sys.exit(1)

    # Remove any modules not requested by user
    modules_to_use = all_modules_list()

    optional_modules = optional_modules_list()
    for feature in list(optional_modules.keys()):
        if feature in requested_features:
            pass
        else:
            for m in optional_modules[feature]:
                modules_to_use.remove(m)

    # Some modules depend on more than one feature
    # We have to check if all features that the module depends on are
    # specified before removing it
    cross_feature_modules = cross_feature_modules_list()
    for feature_group in list(cross_feature_modules.keys()):
        if all(feature in requested_features
               for feature in feature_group):
            pass
        else:
            for m in cross_feature_modules[feature_group]:
                modules_to_use.remove(m)

    return modules_to_use


def load_modules(modules_to_use):
    """
    :param modules_to_use: a list of the names of the modules to use
    :return: list of imported modules (Python <class 'module'> objects)

    Load the requested modules and return them as a list of Python module
    objects.
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
