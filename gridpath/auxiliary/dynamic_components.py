#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Lists and dictionaries of the names of the model dynamic components
"""

from builtins import object

required_capacity_modules = "required_capacity_modules"
capacity_type_operational_period_sets = "capacity_type_operational_period_sets"
storage_only_capacity_type_operational_period_sets = \
    "storage_only_capacity_type_operational_period_sets"
required_operational_modules = "required_operational_modules"
required_prm_modules = "required_prm_modules"
required_reserve_modules = "required_reserve_modules"

headroom_variables = "headroom_variables"
footroom_variables = "footroom_variables"
reserve_variable_derate_params = "reserve_variable_derate_params"
reserve_to_energy_adjustment_params = \
    "reserve_to_energy_adjustment_params"

prm_cost_group_sets = "prm_cost_groups"
prm_cost_group_prm_type = "prm_cost_group_prm_type"

required_tx_capacity_modules = "required_tx_capacity_modules"

load_balance_production_components = "load_balance_production_components"
load_balance_consumption_components = "load_balance_consumption_components"

carbon_cap_balance_emission_components = \
    "carbon_cap_balance_emission_components"

prm_balance_provision_components = \
    "prm_balance_provision_components"
local_capacity_balance_provision_components = \
    "local_capacity_balance_provision_components"

total_cost_components = "total_cost_components"


# TODO: should we have more than one of these depending on component type
class DynamicComponents(object):
    """
    Will contain the dynamic inputs that modules will populate, which will be
    used to initialize model components
    """
    def __init__(self):
        """
        Initiate the dynamic components
        """

        # Capacity-type modules
        setattr(self, required_capacity_modules, list())
        # Capacity-type modules will populate this list if called
        setattr(self, capacity_type_operational_period_sets, list())
        setattr(self, storage_only_capacity_type_operational_period_sets,
                list())

        # Operational type modules
        setattr(self, required_operational_modules, list())

        # PRM type modules
        setattr(self, required_prm_modules, list())

        # Reserve types
        # Will be determined based on whether the user has specified a module
        setattr(self, required_reserve_modules, list())

        # Headroom and footroom variables
        setattr(self, headroom_variables, dict())
        setattr(self, footroom_variables, dict())
        setattr(self, reserve_variable_derate_params, dict())
        setattr(self, reserve_to_energy_adjustment_params, dict())

        # PRM cost groups
        setattr(self, prm_cost_group_sets, list())
        setattr(self, prm_cost_group_prm_type, dict())

        # Transmission
        setattr(self, required_tx_capacity_modules, list())

        # Load balance
        # Modules will add component names to these lists
        setattr(self, load_balance_production_components, list())
        setattr(self, load_balance_consumption_components, list())

        # Carbon cap constraint
        # Modules will add component names to these lists
        setattr(self, carbon_cap_balance_emission_components, list())

        # PRM constraint
        # Modules will add component names to this list
        setattr(self, prm_balance_provision_components, list())

        # Local capacity constraint
        # Modules will add component names to this list
        setattr(self, local_capacity_balance_provision_components, list())

        # Objective function
        # Modules will add component names to this list
        setattr(self, total_cost_components, list())
