Optional Features
=================

GridPath models can include or exclude several high-level level optional
"features." Features include modules from different packages.


Fuels
-----
Whether or not fuel-based projects are included in the model.

Feature modules include:
.. automodule:: gridpath.project.fuels
    :members:
.. automodule:: gridpath.project.operations.fuel_burn
    :members:


Multi-stage
-----------
Whether or not to model multiple stages in production-cost simulation mode.

Feature modules include:
.. automodule:: gridpath.project.operations.fix_commitment
    :members:


Transmission
------------
Whether or not to model transmission between load zones.

Feature modules include:
.. automodule:: gridpath.transmission.__init__
    :members:
.. automodule:: gridpath.transmission.capacity.capacity_types
    :members:
.. automodule:: gridpath.transmission.capacity.capacity
    :members:
.. automodule:: gridpath.transmission.operations.operations
    :members:
.. automodule:: gridpath.system.load_balance.aggregate_transmission_power
    :members:


Transmission Hurdle Rates
-------------------------
Whether or not to apply hurdle rates on transmission line flows.

Feature modules include:
.. automodule:: gridpath.transmission.operations.hurdle_costs
    :members:
.. automodule:: gridpath.objective.transmission.aggregate_hurdle_costs
    :members:


Reserves
--------
Whether or not to model load-following up reserves.

Load-Following Reserves Up
^^^^^^^^^^^^^^^^^^^^^^^^^^

Feature modules include:
.. automodule:: gridpath.geography.load_following_up_balancing_areas
    :members:
.. automodule:: gridpath.system.reserves.requirement.lf_reserves_up
    :members:
.. automodule:: gridpath.project.operations.reserves.lf_reserves_up
    :members:
.. automodule:: gridpath.project.operations.reserves.op_type_dependent.lf_reserves_up
    :members:
.. automodule:: gridpath.system.reserves.aggregation.lf_reserves_up
    :members:
.. automodule:: gridpath.system.reserves.balance.lf_reserves_up
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.lf_reserves_up
    :members:


Load-Following Reserves Down
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Whether or not to model load-following down reserves.

Feature modules include:
.. automodule:: gridpath.geography.load_following_down_balancing_areas
    :members:
.. automodule:: gridpath.system.reserves.requirement.lf_reserves_down
    :members:
.. automodule:: gridpath.project.operations.reserves.lf_reserves_down
    :members:
.. automodule:: gridpath.project.operations.reserves.op_type_dependent.lf_reserves_down
    :members:
.. automodule:: gridpath.system.reserves.aggregation.lf_reserves_down
    :members:
.. automodule:: gridpath.system.reserves.balance.lf_reserves_down
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.lf_reserves_down
    :members:


Regulation Reserves Up
^^^^^^^^^^^^^^^^^^^^^^
Whether or not to model regulation up reserves.

Feature modules include:
.. automodule:: gridpath.geography.regulation_up_balancing_areas
    :members:
.. automodule:: gridpath.system.reserves.requirement.regulation_up
    :members:
.. automodule:: gridpath.project.operations.reserves.regulation_up
    :members:
.. automodule:: gridpath.project.operations.reserves.op_type_dependent.regulation_up
    :members:
.. automodule:: gridpath.system.reserves.aggregation.regulation_up
    :members:
.. automodule:: gridpath.system.reserves.balance.regulation_up
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.regulation_up
    :members:


Regulation Reserves Down
^^^^^^^^^^^^^^^^^^^^^^^^
Whether or not to model regulation down reserves.

Feature modules include:
.. automodule:: gridpath.geography.regulation_down_balancing_areas
    :members:
.. automodule:: gridpath.system.reserves.requirement.regulation_down
    :members:
.. automodule:: gridpath.project.operations.reserves.regulation_down
    :members:
.. automodule:: gridpath.project.operations.reserves.op_type_dependent.regulation_down
    :members:
.. automodule:: gridpath.system.reserves.aggregation.regulation_down
    :members:
.. automodule:: gridpath.system.reserves.balance.regulation_down
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.regulation_down
    :members:


Frequency Response
^^^^^^^^^^^^^^^^^^
Whether or not to model frequency response.

Feature modules include:
.. automodule:: gridpath.geography.frequency_response_balancing_areas
    :members:
.. automodule:: gridpath.system.reserves.requirement.frequency_response
    :members:
.. automodule:: gridpath.project.operations.reserves.frequency_response
    :members:
.. automodule:: gridpath.project.operations.reserves.op_type_dependent.frequency_response
    :members:
.. automodule:: gridpath.system.reserves.aggregation.frequency_response
    :members:
.. automodule:: gridpath.system.reserves.balance.frequency_response
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.frequency_response
    :members:


Spinning Reserves
^^^^^^^^^^^^^^^^^
Whether or not to model spinning reserves.

Feature modules include:
.. automodule:: gridpath.geography.spinning_reserves_balancing_areas
    :members:
.. automodule:: gridpath.system.reserves.requirement.spinning_reserves
    :members:
.. automodule:: gridpath.project.operations.reserves.spinning_reserves
    :members:
.. automodule:: gridpath.project.operations.reserves.op_type_dependent.spinning_reserves
    :members:
.. automodule:: gridpath.system.reserves.aggregation.spinning_reserves
    :members:
.. automodule:: gridpath.system.reserves.balance.spinning_reserves
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.spinning_reserves


Inertia Reserves
^^^^^^^^^^^^^^^^^
Whether or not to model spinning reserves.

Feature modules include:
.. automodule:: gridpath.geography.inertia_reserves_balancing_areas
    :members:
.. automodule:: gridpath.system.reserves.requirement.inertia_reserves
    :members:
.. automodule:: gridpath.project.operations.reserves.inertia_reserves
    :members:
.. automodule:: gridpath.project.operations.reserves.op_type_dependent.inertia_reserves
    :members:
.. automodule:: gridpath.system.reserves.aggregation.inertia_reserves
    :members:
.. automodule:: gridpath.system.reserves.balance.inertia_reserves
    :members:
.. automodule:: gridpath.objective.system.reserve_violation_penalties.inertia_reserves
    :members:


Energy Targets, e.g. Renewable Portfolio Standard (RPS)
-------------------------------------------------------
Whether or not to enforce an energy target policy, e.g. a Renewables
Portfolio Standard (RPS).

Feature modules for period-level targets include:
.. automodule:: gridpath.geography.energy_target_zones
    :members:
.. automodule:: gridpath.system.policy.energy_target.period_energy_target
    :members:
.. automodule:: gridpath.project.operations.energy_target_contributions
    :members:
.. automodule:: gridpath.system.policy.energy_target.aggregate_period_energy_target_contributions
    :members:
.. automodule:: gridpath.system.policy.energy_target.period_energy_target_balance
    :members:
.. automodule:: objective.system.policy.energy_target.aggregate_period_energy_target_violation_penalties
    :members:


Instantaneous penetration
-------------------------
Whether or not to enforce an instantaneous penetration policy

Feature modules for period-level targets include:
.. automodule:: gridpath.geography.instantaneous_penetration_zones
    :members:
.. automodule:: gridpath.system.policy.instantaneous_penetration.instantaneous_penetration_requirements
    :members:
.. automodule:: gridpath.project.operations.instantaneous_penetration_contributions
    :members:
.. automodule:: gridpath.system.policy.instantaneous_penetration.instantaneous_penetration_aggregation
    :members:
.. automodule:: gridpath.system.policy.instantaneous_penetration.instantaneous_penetration_balance
    :members:
.. automodule:: objective.system.policy.aggregate_instantaneous_penetration_violation_penalties
    :members:


Carbon Emissions Cap
--------------------
Whether or not to enforce a carbon cap.

Feature modules include:
.. automodule:: gridpath.geography.carbon_cap_zones
    :members:
.. automodule:: gridpath.system.policy.carbon_cap.carbon_cap
    :members:
.. automodule:: gridpath.project.operations.carbon_emissions
    :members:
.. automodule:: gridpath.system.policy.carbon_cap.aggregate_project_carbon_emissions
    :members:
.. automodule:: gridpath.system.policy.carbon_cap.carbon_balance
    :members:


Planning Reserve Margin (PRM)
-----------------------------
Whether or not to enforce a planning reserve margin constraint.

Feature modules include:
.. automodule:: gridpath.geography.prm_zones
    :members:
.. automodule:: gridpath.system.reliability.prm.prm_requirement
    :members:
.. automodule:: gridpath.project.reliability.prm
    :members:
.. automodule:: gridpath.project.reliability.prm.prm_types
    :members:
.. automodule:: gridpath.project.reliability.prm.prm_simple
    :members:
.. automodule:: gridpath.project.reliability.prm.group_costs
    :members:
.. automodule:: gridpath.system.reliability.prm.aggregate_project_simple_prm_contribution
    :members:
.. automodule:: gridpath.system.reliability.prm.prm_balance
    :members:
.. automodule:: gridpath.objective.project.aggregate_prm_group_costs
    :members:


Local Capacity Requirements
---------------------------
Whether or not to enforce a local capacity requirement constraint.

Feature modules include:
.. automodule:: gridpath.geography.local_capacity_zones
    :members:
.. automodule:: gridpath.system.reliability.local_capacity.local_capacity_requirement
    :members:
.. automodule:: gridpath.project.reliability.local_capacity
    :members:
.. automodule:: gridpath.project.reliability.local_capacity.local_capacity_contribution
    :members:
.. automodule:: gridpath.system.reliability.local_capacity.aggregate_local_capacity_contribution
    :members:
.. automodule:: gridpath.system.reliability.local_capacity.local_capacity_balance
    :members:
.. automodule:: gridpath.objective.system.local_capacity.aggregate_local_capacity_violation_penalties
    :members:


Carbon-Imports Tracking
-----------------------
Whether or not to track how much carbon emissions are imported into a load
zone via transmission, i.e. by applying an emissions intensity on transmission
flows. This feature can only be used if the "Transmission" and "Carbon Cap"
features are enabled.

Feature modules include:
.. automodule:: gridpath.system.policy.carbon_cap.aggregate_transmission_carbon_emissions
    :members:
.. automodule:: gridpath.transmission.operations.carbon_emissions
    :members:
.. automodule:: gridpath.objective.transmission.carbon_imports_tuning_costs
    :members:


Simultaneous Flow Limits
------------------------
Whether or not to constrain simultaneous flows on groups of transmission
lines. This feature can only be used if the "Transmission" feature is enabled.

Feature modules include:
.. automodule:: gridpath.transmission.operations.simultaneous_flow_limits
    :members:


ELCC Surface
------------
Whether or not to use an "ELCC surface" approach to track the ELCC
contribution of certain generators (e.g. variable generators such as wind and
solar). This feature can only be used if the "PRM" feature is enabled.

Feature modules include:
.. automodule:: gridpath.project.reliability.prm.elcc_surface
    :members:
.. automodule:: gridpath.system.reliability.prm.elcc_surface
    :members:
.. automodule:: gridpath.objective.system.prm.dynamic_elcc_tuning_penalties
    :members:
