#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module creates the DynamicComponents class, which contains the lists and
dictionaries of the names of GridPath dynamic components. These are
components that are populated by other GridPath modules based on the
scenario input data.
"""

from builtins import object

# Create global variables for the dynamic component names, so that we can
# more easily import the correct names into other modules
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


# TODO: should we have more than one of these depending on component type,
#  e.g. a group for GP modules to use (e.g. capacity and operational types,
#  prm modules, reserve modules) vs. actual optimizaton model components such
#  as the headroom and footroom variables vs. the names of constraint
#  components
class DynamicComponents(object):
    """
    Here we initialize the class object and its components that will contain
    the dynamic inputs. When called, the GridPath modules will populate the
    various class components based on the input data, which will then be
    used to initialize model components, keep track of required submodules,
    keep track of components added by modules to dynamic constraints, etc.
    """
    def __init__(self):
        """
        Initialize the dynamic components.
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

        # Load balance constraint
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
