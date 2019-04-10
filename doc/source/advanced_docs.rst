*******************
Basic Functionality
*******************

This chapter describes GridPath's basic functionality if no optional
features are included.

Temporal Setup
==============

gridpath.temporal
-----------------
.. automodule:: gridpath.temporal.__init__

gridpath.temporal.operations
----------------------------
.. automodule:: gridpath.temporal.operations.__init__

gridpath.temporal.operations.timepoints
---------------------------------------
.. automodule:: gridpath.temporal.operations.timepoints
    :members: add_model_components

gridpath.temporal.operations.horizons
-------------------------------------
.. automodule:: gridpath.temporal.operations.horizons
    :members: add_model_components

gridpath.temporal.investment
----------------------------
.. automodule:: gridpath.temporal.investment.__init__

gridpath.temporal.investment.periods
------------------------------------
.. automodule:: gridpath.temporal.investment.periods
    :members: add_model_components


Geographic Setup
================
.. automodule:: gridpath.geography.__init__

gridpath.geography.load_zones
-----------------------------
.. automodule:: gridpath.geography.load_zones
    :members: add_model_components

Projects
========

gridpath.project.__init__
^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.__init__
    :members: determine_dynamic_components, add_model_components

Project Capacity
----------------

gridpath.project.capacity
^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.__init__

gridpath.project.capacity.capacity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.capacity
    :members: add_model_components

gridpath.project.capacity.costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.costs
    :members: add_model_components

gridpath.project.capacity.capacity_types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.capacity_types.__init__

gridpath.project.capacity.capacity_types.existing_gen_no_economic_retirement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.capacity_types.existing_gen_no_economic_retirement
    :members: add_module_specific_components, capacity_rule, capacity_cost_rule

gridpath.project.capacity.capacity_types.new_build_generator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.capacity_types.new_build_generator
    :members: add_module_specific_components, capacity_rule, capacity_cost_rule

gridpath.project.capacity.capacity_types.existing_gen_linear_economic_retirement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.capacity_types.existing_gen_linear_economic_retirement
    :members: add_module_specific_components, capacity_rule, capacity_cost_rule

gridpath.project.capacity.capacity_types.storage_specified_no_economic_retirement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.capacity_types.storage_specified_no_economic_retirement
    :members: add_module_specific_components, capacity_rule, energy_capacity_rule, capacity_cost_rule

gridpath.project.capacity.capacity_types.new_build_storage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.capacity_types.new_build_storage
    :members: add_module_specific_components, capacity_rule, energy_capacity_rule, capacity_cost_rule

gridpath.project.capacity.capacity_types.new_shiftable_load_supply_curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.capacity.capacity_types.new_shiftable_load_supply_curve
    :members: add_module_specific_components, capacity_rule, energy_capacity_rule, capacity_cost_rule


Project Operations
------------------

gridpath.project.operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.__init__

gridpath.project.operations.power
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.power
    :members: add_model_components

gridpath.project.operations.costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.costs
    :members: add_model_components

gridpath.project.capacity.operational_types.must_run
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.must_run
    :members: power_provision_rule

gridpath.project.capacity.operational_types.always_on
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.always_on
    :members: add_module_specific_components, power_provision_rule

gridpath.project.capacity.operational_types.dispatchable_binary_commit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.dispatchable_binary_commit
    :members: add_module_specific_components, power_provision_rule

gridpath.project.capacity.operational_types.dispatchable_capacity_commit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.dispatchable_capacity_commit
    :members: add_module_specific_components, power_provision_rule

gridpath.project.capacity.operational_types.hydro_noncurtailable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.hydro_noncurtailable
    :members: add_module_specific_components, power_provision_rule

gridpath.project.capacity.operational_types.variable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.variable
    :members: add_module_specific_components, power_provision_rule

gridpath.project.capacity.operational_types.storage_generic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.storage_generic
    :members: add_module_specific_components, power_provision_rule

gridpath.project.capacity.operational_types.shiftable_load_generic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.shiftable_load_generic


Load Balance
============

gridpath.system.load_balance.static_load_requirement
----------------------------------------------------
.. automodule:: gridpath.system.load_balance.static_load_requirement
    :members: add_model_components

gridpath.system.load_balance.aggregate_project_power
----------------------------------------------------
.. automodule:: gridpath.system.load_balance.aggregate_project_power
    :members: add_model_components

gridpath.system.load_balance.load_balance
-----------------------------------------
.. automodule:: gridpath.system.load_balance.load_balance
    :members: add_model_components


Objective Function
==================
.. automodule:: gridpath.objective.__init__

.. automodule:: gridpath.objective.project.__init__

.. automodule:: gridpath.objective.system.__init__

gridpath.objective.project.aggregate_capacity_costs
---------------------------------------------------
.. automodule:: gridpath.objective.project.aggregate_capacity_costs
    :members: add_model_components

gridpath.objective.project.aggregate_operational_costs
------------------------------------------------------
.. automodule:: gridpath.objective.project.aggregate_operational_costs
    :members: add_model_components

gridpath.objective.system.aggregate_load_balance_penalties
----------------------------------------------------------
.. automodule:: gridpath.objective.system.aggregate_load_balance_penalties
    :members: add_model_components

gridpath.objective.min_total_cost
---------------------------------
.. automodule:: gridpath.objective.min_total_cost
    :members: add_model_components



**********************
Advanced Functionality
**********************

This section describes GridPath's advanced functionality that can be included
by selecting optional features.

Multi-Stage
============
.. automodule:: gridpath.project.operations.fix_commitment

Transmission
============

gridpath.transmission
---------------------
.. automodule:: gridpath.transmission.__init__

gridpath.transmission.capacity.capacity_types
---------------------------------------------
.. automodule:: gridpath.transmission.capacity.capacity_types

gridpath.transmission.capacity.capacity
---------------------------------------
.. automodule:: gridpath.transmission.capacity.capacity

gridpath.transmission.operations.operations
-------------------------------------------
.. automodule:: gridpath.transmission.operations.operations

gridpath.system.load_balance.aggregate_transmission_power
---------------------------------------------------------
.. automodule:: gridpath.system.load_balance.aggregate_transmission_power

Transmission Hurdle Rates
-------------------------
If the transmission hurdle rates feature is enabled, the following modules
are also included:

gridpath.transmission.operations.costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.transmission.operations.costs

gridpath.objective.transmission.aggregate_operational_costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.objective.transmission.aggregate_operational_costs



Operating Reserves
==================
GridPath can model operating reserve requirements and provision. Reserves
currently modeled (none, any, or all can be selected, as they are additive
in the model) include regulation up and down, spinning reserves,
load-following up and down, and frequency response.

The treatment of operating reserves is standardized. It requires defining
the reserve balancing areas with their associated parameters and setting
the reserve requirements by balancing area and timepoint; we must
also assign a balancing area to each project that can provide the reserve;
the model then takes care of creating the appropriate project-level
reserve-provision variables, aggregates the provision of reserves, and
ensures that total provision of the reserve and the reserve requirement are
balanced (or that penalties are applied if not).

Modules from each reserve feature call on standardized methods included in
other GridPath modules. The standard methods are included in the following
modules:

gridpath.project.operations.reserves.reserve_provision
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: gridpath.project.operations.reserves.reserve_provision
    :members: generic_determine_dynamic_components



Reliability
===========
GridPath currently includes the ability to require that a planning reserve
requirement be met.

More documentation will be included in the future.

Policy
======

GridPath includes the ability to model certain policies, e.g. a renewable
portfolio standard requiring that a certain percentage of demand be met with
renewable resources, and a carbon cap, requiring that total emissions be
below a certain level.

More documentation will be included in the future.

Custom Modules
==============

GridPath can include custom modules.
