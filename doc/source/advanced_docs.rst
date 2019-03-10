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
.. automodule:: gridpath.project.__init__
    :members: add_model_components

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

gridpath.project.capacity.operational_types.always_on
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.always_on

gridpath.project.capacity.operational_types.dispatchable_binary_commit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.dispatchable_binary_commit
    :members: add_module_specific_components

gridpath.project.capacity.operational_types.dispatchable_capacity_commit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.dispatchable_capacity_commit

gridpath.project.capacity.operational_types.hydro_curtailable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.hydro_curtailable

gridpath.project.capacity.operational_types.variable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.variable

gridpath.project.capacity.operational_types.storage_generic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.storage_generic

gridpath.project.capacity.operational_types.shiftable_load_generic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: gridpath.project.operations.operational_types.shiftable_load_generic

Load Balance
============

Objective Function
==================

**********************
Advanced Functionality
**********************

This section describes GridPath's advanced functionality that can be included
by selecting optional features.

Multli-Stage
============

Transmission
============

Operating Reserves
==================

Reliability
===========

Policy
======

Custom Modules
==============
