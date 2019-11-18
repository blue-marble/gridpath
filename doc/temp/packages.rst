Packages
========

GridPath consists of several high-level 'packages,' each containing multiple
modules.

gridpath.auxiliary
------------------

This package contains various modules that provide auxiliary methods used by
the other modules as well as the overall model structure.

.. automodule:: gridpath.auxiliary.__init__
    :members:
.. automodule:: gridpath.auxiliary.auxiliary
    :members:
.. automodule:: gridpath.auxiliary.dynamic_components
    :members:
.. automodule:: gridpath.auxiliary.module_list
    :members:
.. automodule:: gridpath.auxiliary.scenario_chars
    :members:

gridpath.temporal
-----------------
Modules in this package define the temporal span and resolution of the model.
.. automodule:: gridpath.temporal.__init__
    :members:
.. automodule:: gridpath.temporal.investment.__init__
    :members:
.. automodule:: gridpath.temporal.investment.periods
    :members:
.. automodule:: gridpath.temporal.operations.__init__
    :members:
.. automodule:: gridpath.temporal.operations.horizons
    :members:
.. automodule:: gridpath.temporal.operations.timepoints
    :members:

gridpath.geography
------------------

Modules in this package define the geographic span and resolution of the model.

.. automodule:: gridpath.geography.__init__
    :members:
.. automodule:: gridpath.geography.load_zones
    :members:
.. automodule:: gridpath.geography.load_following_up_balancing_areas
    :members:
.. automodule:: gridpath.geography.load_following_down_balancing_areas
    :members:
.. automodule:: gridpath.geography.regulation_up_balancing_areas
    :members:
.. automodule:: gridpath.geography.regulation_down_balancing_areas
    :members:
.. automodule:: gridpath.geography.frequency_response_balancing_areas
    :members:
.. automodule:: gridpath.geography.spinning_reserves_balancing_areas
    :members:
.. automodule:: gridpath.geography.rps_zones
    :members:
.. automodule:: gridpath.geography.carbon_cap_zones
    :members:
.. automodule:: gridpath.geography.prm_zones
    :members:
.. automodule:: gridpath.geography.local_capacity_zones
    :members:

gridpath.project
----------------

Modules in this package define the characteristics of the generation,
storage and demand-side resources available to the model.

.. automodule:: gridpath.project.__init__
    :members:
.. automodule:: gridpath.project.fuels
    :members:
.. automodule:: gridpath.project.capacity.__init__
    :members:
.. automodule:: gridpath.project.capacity.capacity_types.__init__
    :members:
.. automodule:: gridpath.project.capacity.capacity_types.common_methods
    :members:
.. automodule:: gridpath.project.capacity.capacity_types.
existing_gen_linear_economic_retirement
    :members:
.. automodule:: gridpath.project.capacity.capacity_types.
existing_gen_no_economic_retirement
    :members:
.. automodule:: gridpath.project.capacity.capacity_types.new_build_generator
    :members:
.. automodule:: gridpath.project.capacity.capacity_types.new_build_storage
    :members:
.. automodule:: gridpath.project.capacity.capacity_types.
new_shiftable_load_supply_curve
    :members:
.. automodule:: gridpath.project.capacity.capacity_types.
storage_specified_no_economic_retirement
    :members:
.. automodule:: gridpath.project.capacity.capacity
    :members:
.. automodule:: gridpath.project.capacity.costs
    :members:
.. automodule:: gridpath.project.operations.__init__
    :members:
.. automodule:: gridpath.project.operations.operational_types.__init__
    :members:
.. automodule:: gridpath.project.operations.operational_types.always_on
    :members:
.. automodule:: gridpath.project.operations.operational_types.
dispatchable_binary_commit
    :members:
.. automodule:: gridpath.project.operations.operational_types.
dispatchable_capacity_commit
    :members:
.. automodule:: gridpath.project.operations.operational_types.
dispatchable_continuous_commit
    :members:
.. automodule:: gridpath.project.operations.operational_types.
dispatchable_no_commit
    :members:
.. automodule:: gridpath.project.operations.operational_types.hydro_curtailable
    :members:
.. automodule:: gridpath.project.operations.operational_types.
hydro_noncurtailable
    :members:
.. automodule:: gridpath.project.operations.operational_types.must_run
    :members:
.. automodule:: gridpath.project.operations.operational_types.
shiftable_load_generic
    :members:
.. automodule:: gridpath.project.operations.operational_types.storage_generic
    :members:
.. automodule:: gridpath.project.operations.operational_types.variable
    :members:
.. automodule:: gridpath.project.operations.operational_types.
variable_no_curtailment
    :members:
.. automodule:: gridpath.project.operations.reserves.__init__
    :members:
.. automodule:: gridpath.project.operations.reserves.reserve_provision
    :members:
.. automodule:: gridpath.project.operations.reserves.lf_reserves_up
    :members:
.. automodule:: gridpath.project.operations.reserves.lf_reserves_down
    :members:
.. automodule:: gridpath.project.operations.reserves.regulation_up
    :members:
.. automodule:: gridpath.project.operations.reserves.regulation_down
    :members:
.. automodule:: gridpath.project.operations.reserves.frequency_response
    :members:
.. automodule:: gridpath.project.operations.reserves.spinning_reserves
    :members:
.. automodule:: gridpath.project.operations.reserves.
subhourly_energy_adjustment
    :members:
.. automodule:: gridpath.project.operations.fix_commitment
    :members:
.. automodule:: gridpath.project.operations.power
    :members:
.. automodule:: gridpath.project.operations.costs
    :members:
.. automodule:: gridpath.project.operations.fuel_burn
    :members:
.. automodule:: gridpath.project.operations.recs
    :members:
.. automodule:: gridpath.project.operations.carbon_emissions
    :members:
.. automodule:: gridpath.project.operations.tuning_costs
    :members:
.. automodule:: gridpath.project.reliability.__init__
    :members:
.. automodule:: gridpath.project.reliability.prm.__init__
    :members:
.. automodule:: gridpath.project.reliability.prm.prm_types.__init__
    :members:
.. automodule:: gridpath.project.reliability.prm.prm_types.energy_only_allowed
    :members:
.. automodule:: gridpath.project.reliability.prm.prm_types.fully_deliverable
    :members:
.. automodule:: gridpath.project.reliability.prm.prm_types.
fully_deliverable_energy_limited
    :members:
.. automodule:: gridpath.project.reliability.prm.prm_simple
    :members:
.. automodule:: gridpath.project.reliability.prm.elcc_surface
    :members:
.. automodule:: gridpath.project.reliability.prm.group_costs
    :members:
.. automodule:: gridpath.project.reliability.local_capacity.__init__
    :members:
.. automodule:: gridpath.project.reliability.local_capacity.
local_capacity_contribution
    :members:

gridpath.transmission
---------------------

Modules in this package define the characteristics of the transmission
infrastructure available to the model.

.. automodule:: gridpath.transmission.__init__
    :members:
.. automodule:: gridpath.transmission.capacity.__init__
    :members:
.. automodule:: gridpath.transmission.capacity.capacity_types.__init__
    :members:
.. automodule:: gridpath.transmission.capacity.capacity_types.
specified_transmission
    :members:
.. automodule:: gridpath.transmission.capacity.capacity_types.
new_build_transmission
    :members:
.. automodule:: gridpath.transmission.capacity.capacity
    :members:
.. automodule:: gridpath.transmission.operations.__init__
    :members:
.. automodule:: gridpath.transmission.operations.operations
    :members:
.. automodule:: gridpath.transmission.operations.costs
    :members:
.. automodule:: gridpath.transmission.operations.simultaneous_flow_limits
    :members:
.. automodule:: gridpath.transmission.operations.carbon_emissions
    :members:

gridpath.system
---------------
Modules in this package define system-level parameters and constraints.

.. automodule:: gridpath.system.__init__
    :members:
.. automodule:: gridpath.system.load_balance.__init__
    :members:
.. automodule:: gridpath.system.load_balance.static_load_requirement
    :members:
.. automodule:: gridpath.system.load_balance.aggregate_project_power
    :members:
.. automodule:: gridpath.system.load_balance.aggregate_transmission_power
    :members:
.. automodule:: gridpath.system.load_balance.load_balance
    :members:
.. automodule:: gridpath.system.reserves.__init__
    :members:
.. automodule:: gridpath.system.reserves.requirement.reserve_requirements
    :members:
.. automodule:: gridpath.system.reserves.requirement.lf_reserves_up
    :members:
.. automodule:: gridpath.system.reserves.requirement.lf_reserves_down
    :members:
.. automodule:: gridpath.system.reserves.requirement.regulation_up
    :members:
.. automodule:: gridpath.system.reserves.requirement.regulation_down
    :members:
.. automodule:: gridpath.system.reserves.requirement.frequency_response
    :members:
.. automodule:: gridpath.system.reserves.requirement.spinning_reserves
    :members:
.. automodule:: gridpath.system.reserves.aggregation.__init__
    :members:
.. automodule:: gridpath.system.reserves.aggregation.reserve_aggregation
    :members:
.. automodule:: gridpath.system.reserves.aggregation.lf_reserves_up
    :members:
.. automodule:: gridpath.system.reserves.aggregation.lf_reserves_down
    :members:
.. automodule:: gridpath.system.reserves.aggregation.regulation_up
    :members:
.. automodule:: gridpath.system.reserves.aggregation.regulation_down
    :members:
.. automodule:: gridpath.system.reserves.aggregation.frequency_response
    :members:
.. automodule:: gridpath.system.reserves.aggregation.spinning_reserves
    :members:
.. automodule:: gridpath.system.reserves.balance.__init__
    :members:
.. automodule:: gridpath.system.reserves.balance.reserve_balance
    :members:
.. automodule:: gridpath.system.reserves.balance.lf_reserves_up
    :members:
.. automodule:: gridpath.system.reserves.balance.lf_reserves_down
    :members:
.. automodule:: gridpath.system.reserves.balance.regulation_up
    :members:
.. automodule:: gridpath.system.reserves.balance.regulation_down
    :members:
.. automodule:: gridpath.system.reserves.balance.frequency_response
    :members:
.. automodule:: gridpath.system.reserves.balance.spinning_reserves
    :members:
.. automodule:: gridpath.system.policy.__init__
    :members:
.. automodule:: gridpath.system.policy.rps.__init__
    :members:
.. automodule:: gridpath.system.policy.rps.rps_requirement
    :members:
.. automodule:: gridpath.system.policy.rps.aggregate_recs
    :members:
.. automodule:: gridpath.system.policy.rps.rps_balance
    :members:
.. automodule:: gridpath.system.policy.carbon_cap.__init__
    :members:
.. automodule:: gridpath.system.policy.carbon_cap.carbon_cap
    :members:
.. automodule:: gridpath.system.policy.carbon_cap.
aggregate_project_carbon_emissions
    :members:
.. automodule:: gridpath.system.policy.carbon_cap.
aggregate_transmission_carbon_emissions
    :members:
.. automodule:: gridpath.system.policy.carbon_cap.carbon_balance
    :members:


gridpath.objective
------------------
Modules in this package add expressions to the objective function.

.. automodule:: gridpath.objective.__init__
    :members:
.. automodule:: gridpath.objective.min_total_cost
    :members:
.. automodule:: gridpath.objective.project.__init__
    :members:
.. automodule:: gridpath.objective.project.aggregate_capacity_costs
    :members:
.. automodule:: gridpath.objective.project.aggregate_operational_costs
    :members:
.. automodule:: gridpath.objective.project.aggregate_operational_tuning_costs
    :members:
.. automodule:: gridpath.objective.project.aggregate_prm_group_costs
    :members:
.. automodule:: gridpath.objective.transmission.__init__
    :members:
.. automodule:: gridpath.objective.transmission.aggregate_operational_costs
    :members:
.. automodule:: gridpath.objective.transmission.carbon_imports_tuning_costs
    :members:
.. automodule:: gridpath.objective.system.__init__
    :members:
.. automodule:: gridpath.objective.system.aggregate_load_balance_penalties
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.__init__
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.
aggregate_reserve_violation_penalties
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.
lf_reserves_up
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.
lf_reserves_down
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.
regulation_up
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.
regulation_down
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.
frequency_response
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.
spinning_reserves
    :members:
.. automodule:: gridpath.objective.system.prm.__init__
    :members:
.. automodule:: gridpath.objective.system.prm.dynamic_elcc_tuning_penalties
    :members:
.. automodule:: gridpath.objective.system.local_capacity.__init__
    :members:
.. automodule:: gridpath.objective.system.local_capacity.
aggregate_local_capacity_violation_penalties
    :members:



