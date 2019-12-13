******************
Database Structure
******************

All tables names in the GridPath database start with one of seven prefixes:
:code:`mod_`, :code:`subscenario_`, :code:`inputs_`, :code:`scenarios`,
:code:`options_`, :code:`status_`, or :code:`ui_`. This structure is meant to
organize the tables by their function. Below are descriptions of each table
type and its role, and of the kind of data tables of this type contain.

The :code:`mod_` Tables
***********************
The :code:`mod_` should not be modified except by developers. These contain
various data used by the GridPath platform to describe available
functionality, help enforce input data consistency and integrity, and aid in
validation.


The :code:`subscenario_` and :code:`inputs_` Tables
***************************************************
Most tables in the GridPath database have the :code:`subscenario_` and
:code:`inputs_` prefix. With a few exceptions, for each :code:`subscenario_`
table, there is a respective :code:`inputs_` table (i.e. the tables have the
same name except for the prefix). This is because the :code:`subscenario_`
tables contain the descriptions of the input data contained in the
:code:`inputs_` tables. For example the :code:`inputs_system_load` may
contain three different load profiles -- low, mid, and high; the
:code:`subscenarios_system_load` will then contain three rows, one for each
load profile, with its description and ID. The pairs of :code:`subscenario_`
and :code:`inputs_` are linked via an ID column: in the case of the system
load tables, that is the :code:`load_scenario_id` column. We call these
shared table keys *subscenario IDs*, as we use them to create a full
GridPath scenario in the :code:`scenarios` table.

The :code:`scenarios` Table
***************************
In GridPath, we use the term 'scenario' to describe a model run with a
particular set of inputs. Some of those inputs stay the same from scenario to
scenario and others we vary to understand their effect on the results. For
example, we could keep some input types like the zonal and transmission
topography, temporal resolution, resource availability, and policy
requirements the same across scenarios, but vary other input types, e.g. the
load profile, the cost of solar, and the operational characteristics of coal,
to create different scenarios. We call each of those inputs types a
'subscenario' since they are the building blocks of a full scenario. In
GridPath, you can create a scenario by populating a row of the
:code:`scenarios` table. The columns of the :code:`scenarios` table are
linked one of the 'building blocks' -- the data in :code:`inputs_` tables --
via the respective *subscenario ID*.

For example, the :code:`load_scenario_id` column of the :code:`scenarios` table
references the :code:`load_scenario_id` column of the
:code:`subscenarios_system_load` table, which in turn determines which load
profile contained in the :code:`inputs_system_load` table the scenario
should use. In our example with three different load profiles, the data for
which are contained in the :code:`inputs_system_load` table,
:code:`subscenarios_system_load` will contain three rows with values of 1,
2, and 3 respectively in the :code:`load_scenario_id` column; in the
:code:`scenarios` table, the user would then be able to select a value of 1,
2, or 3 in the :code:`load_scenario_id` column to determine which load
profile the scenario should use. Similarly, we would select the solar costs
to use in the scenario via the :code:`projects_new_cost_scenario_id` column
of the :code:`scenarios` table (which is linked to the
:code:`subscenarios_project_new_cost` and :code:`inputs_project_new_cost`
tables) and the operational characteristics of coal to use via the
:code:`project_operational_chars_scenario_id` column (which is linked to the
:code:`subscenarios_project_operational_chars` and
:code:`inputs_project_operational_chars` tables).

The :code:`options_` Tables
***************************
Some GridPath run options can be specified via the database in the
:code:`options_` tables. Currently, this includes the solver options that
can be specified for a scenario run

The :code:`status_` Tables
**************************
GridPath keeps track of scenario validation and run status. The scenario
status is recorded in the :code:`scenarios` table (in the
:code:`validation_status_id` and :code:`run_status_id` columns) and an
additional detail can be found in the :code:`status_` tables. Currently,
this includes a single table: the :code:`status_validation` table, which
contains information about errors encountered during validation for each
scenario that has been validated.

The :code:`ui_` Tables
**********************
The :code:`ui_` tables are used to include and exclude components of the
GridPath user interface.

*********************
Building the Database
*********************

.. note:: We'll be expanding this section considerably in the next few weeks.

Temporal Inputs
***************

Relevant tables:

+-------------------------------+----------------------------------------------+
|:code:`scenarios` table column |:code:`temporal_scenario_id`                  |
+-------------------------------+----------------------------------------------+
|:code:`scenario` table feature |N/A                                           |
+-------------------------------+----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_temporal_timepoints`      |
+-------------------------------+----------------------------------------------+
|:code:`input_` tables          |- :code:`inputs_temporal_timepoints`          |
|                               |- :code:`inputs_temporal_horizons`            |
|                               |- :code:`inputs_temporal_horizon_timepoints`  |
|                               |- :code:`inputs_temporal_periods`             |
|                               |- :code:`inputs_temporal_subproblems`         |
|                               |- :code:`inputs_temporal_subproblem_stages`   |
+-------------------------------+----------------------------------------------+

Load Zone Inputs
****************

Relevant tables:

+-------------------------------+----------------------------------------------+
|:code:`scenarios` table column |:code:`load_zone_scenario_id`                 |
+-------------------------------+----------------------------------------------+
|:code:`scenario` table feature |N/A                                           |
+-------------------------------+----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_load_zones`     |
+-------------------------------+----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_load_zones`           |
+-------------------------------+----------------------------------------------+

System Load
***********

Relevant tables:

+-------------------------------+---------------------------------+
|:code:`scenarios` table column |:code:`load_scenario_id`         |
+-------------------------------+---------------------------------+
|:code:`scenario` table feature |N/A                              |
+-------------------------------+---------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_load` |
+-------------------------------+---------------------------------+
|:code:`input_` tables          |:code:`inputs_system_load`       |
+-------------------------------+---------------------------------+


Project Inputs
**************

=================
Project Portfolio
=================

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_portfolio_scenario_id`         |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_portfolios`       |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_portfolios`             |
+--------------------------------+----------------------------------------------+

==================
Specified Projects
==================

Capacity
========

Relevant tables:

+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_existing_capacity_scenario_id`  |
+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table feature |N/A                                            |
+--------------------------------+-----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_existing_capacity` |
+--------------------------------+-----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_existing_capacity`       |
+--------------------------------+-----------------------------------------------+

Fixed Costs
===========

Relevant tables:

+--------------------------------+-------------------------------------------------+
|:code:`scenarios` table column  |:code:`project_existing_fixed_cost_scenario_id`  |
+--------------------------------+-------------------------------------------------+
|:code:`scenarios` table feature |N/A                                              |
+--------------------------------+-------------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_existing_fixed_cost` |
+--------------------------------+-------------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_existing_fixed_cost`       |
+--------------------------------+-------------------------------------------------+


============
New Projects
============

Potential
=========

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_new_potential_scenario_id`     |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_new_potential`    |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_new_potential`          |
+--------------------------------+----------------------------------------------+

Capital Costs
=============

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_new_cost_scenario_id`          |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_new_cost`         |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_new_cost`               |
+--------------------------------+----------------------------------------------+

====================
Project Availability
====================

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_availability_scenario_id`      |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_availability`     |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_availability_types`     |
+--------------------------------+----------------------------------------------+

Endogenous
==========

Relevant tables:

+---------------------------+-----------------------------------------------------+
|:code:`subscenario_` table |:code:`subscenarios_project_availability_endogenous` |
+---------------------------+-----------------------------------------------------+
|:code:`input_` table       |:code:`inputs_project_availability_endogenous`       |
+---------------------------+-----------------------------------------------------+

Exogenous
=========

Relevant tables:

+---------------------------+----------------------------------------------------+
|:code:`subscenario_` table |:code:`subscenarios_project_availability_exogenous` |
+---------------------------+----------------------------------------------------+
|:code:`input_` table       |:code:`inputs_project_availability_exogenous`       |
+---------------------------+----------------------------------------------------+

===================================
Project Operational Characteristics
===================================

Relevant tables:

+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_operational_chars_scenario_id`  |
+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table feature |N/A                                            |
+--------------------------------+-----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_operational_chars` |
+--------------------------------+-----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_operational_chars`       |
+--------------------------------+-----------------------------------------------+

Heat Rates (OPTIONAL)
=====================

Relevant tables:

+---------------------+----------------------------------------------+
|:code:`input_` table |:code:`inputs_project_heat_rate_curves`       |
+---------------------+----------------------------------------------+

Variable Generator Profiles (OPTIONAL)
======================================

Relevant tables:

+---------------------+---------------------------------------------------+
|:code:`input_` table |:code:`inputs_project_variable_generator_profiles` |
+---------------------+---------------------------------------------------+

Hydro Operating Characteristics (OPTIONAL)
==========================================

Relevant tables:

+---------------------+---------------------------------------------------+
|:code:`input_` table |:code:`inputs_project_hydro_operational_chars`     |
+---------------------+---------------------------------------------------+


Transmission Inputs (OPTIONAL)
******************************

Optional inputs needed if transmission feature is enabled for a scenario.

======================
Transmission Portfolio
======================

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_portfolio_scenario_id`         |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                       |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_portfolios`  |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_portfolios`        |
+--------------------------------+----------------------------------------------+

=======================
Transmission Topography
=======================

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_load_zones_scenario_id`   |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                       |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_load_zones`  |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_load_zones`        |
+--------------------------------+----------------------------------------------+

======================
Specified Transmission
======================

Capacity
========

Relevant tables:

+--------------------------------+----------------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_existing_capacity_scenario_id`  |
+--------------------------------+----------------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                             |
+--------------------------------+----------------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_existing_capacity` |
+--------------------------------+----------------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_existing_capacity`       |
+--------------------------------+----------------------------------------------------+


================
New Transmission
================

Capital Costs
=============

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_new_cost_scenario_id`     |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                       |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_new_cost`    |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_new_cost`          |
+--------------------------------+----------------------------------------------+

========================================
Transmission Operational Characteristics
========================================

+--------------------------------+----------------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_operational_chars_scenario_id`  |
+--------------------------------+----------------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                             |
+--------------------------------+----------------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_operational_chars` |
+--------------------------------+----------------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_operational_chars`       |
+--------------------------------+----------------------------------------------------+


Fuel Inputs (OPTIONAL)
**********************

====================
Fuel Characteristics
====================

Relevant tables:

+--------------------------------+-----------------------------------+
|:code:`scenarios` table column  |:code:`fuel_scenario_id`           |
+--------------------------------+-----------------------------------+
|:code:`scenarios` table feature |:code:`of_fuels`                   |
+--------------------------------+-----------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_fuels` |
+--------------------------------+-----------------------------------+
|:code:`input_` tables           |:code:`inputs_project_fuels`       |
+--------------------------------+-----------------------------------+

===========
Fuel Prices
===========

Relevant tables:

+--------------------------------+-----------------------------------------+
|:code:`scenarios` table column  |:code:`fuel_price_scenario_id`           |
+--------------------------------+-----------------------------------------+
|:code:`scenarios` table feature |:code:`of_fuels`                         |
+--------------------------------+-----------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_fuel_prices` |
+--------------------------------+-----------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_fuel_prices`       |
+--------------------------------+-----------------------------------------+


Reserves (OPTIONAL)
*******************

=============
Regulation Up
=============

Balancing Areas
===============

Relevant tables:

+-------------------------------+-------------------------------------------------+
|:code:`scenarios` table column |:code:`regulation_up_ba_scenario_id`             |
+-------------------------------+-------------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_up`                         |
+-------------------------------+-------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_regulation_up_bas` |
+-------------------------------+-------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_regulation_up_bas`       |
+-------------------------------+-------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+-----------------------------------------------+
|:code:`scenarios` table column |:code:`project_regulation_up_ba_scenario_id`   |
+-------------------------------+-----------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_up`                       |
+-------------------------------+-----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_regulation_up_bas` |
+-------------------------------+-----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_regulation_up_bas`       |
+-------------------------------+-----------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+------------------------------------------+
|:code:`scenarios` table column |:code:`regulation_up_scenario_id`         |
+-------------------------------+------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_up`                  |
+-------------------------------+------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_regulation_up` |
+-------------------------------+------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_regulation_up`       |
+-------------------------------+------------------------------------------+

===============
Regulation Down
===============

Balancing Areas
===============

Relevant tables:

+-------------------------------+---------------------------------------------------+
|:code:`scenarios` table column |:code:`regulation_down_ba_scenario_id`             |
+-------------------------------+---------------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_down`                         |
+-------------------------------+---------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_regulation_down_bas` |
+-------------------------------+---------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_regulation_down_bas`       |
+-------------------------------+---------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+-------------------------------------------------+
|:code:`scenarios` table column |:code:`project_regulation_down_ba_scenario_id`   |
+-------------------------------+-------------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_down`                       |
+-------------------------------+-------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_regulation_down_bas` |
+-------------------------------+-------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_regulation_down_bas`       |
+-------------------------------+-------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+--------------------------------------------+
|:code:`scenarios` table column |:code:`regulation_down_scenario_id`         |
+-------------------------------+--------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_down`                  |
+-------------------------------+--------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_regulation_down` |
+-------------------------------+--------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_regulation_down`       |
+-------------------------------+--------------------------------------------+

=================
Spinning Reserves
=================

Balancing Areas
===============

Relevant tables:

+-------------------------------+-----------------------------------------------------+
|:code:`scenarios` table column |:code:`spinning_reserves_ba_scenario_id`             |
+-------------------------------+-----------------------------------------------------+
|:code:`scenario` table feature |:code:`of_spinning_reserves`                         |
+-------------------------------+-----------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_spinning_reserves_bas` |
+-------------------------------+-----------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_spinning_reserves_bas`       |
+-------------------------------+-----------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+---------------------------------------------------+
|:code:`scenarios` table column |:code:`project_spinning_reserves_ba_scenario_id`   |
+-------------------------------+---------------------------------------------------+
|:code:`scenario` table feature |:code:`of_spinning_reserves`                       |
+-------------------------------+---------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_spinning_reserves_bas` |
+-------------------------------+---------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_spinning_reserves_bas`       |
+-------------------------------+---------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+----------------------------------------------+
|:code:`scenarios` table column |:code:`spinning_reserves_scenario_id`         |
+-------------------------------+----------------------------------------------+
|:code:`scenario` table feature |:code:`of_spinning_reserves`                  |
+-------------------------------+----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_spinning_reserves` |
+-------------------------------+----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_spinning_reserves`       |
+-------------------------------+----------------------------------------------+

==========================
Load-Following Reserves Up
==========================

Balancing Areas
===============

Relevant tables:

+-------------------------------+--------------------------------------------------+
|:code:`scenarios` table column |:code:`lf_reserves_up_ba_scenario_id`             |
+-------------------------------+--------------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_up`                         |
+-------------------------------+--------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_lf_reserves_up_bas` |
+-------------------------------+--------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_lf_reserves_up_bas`       |
+-------------------------------+--------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+------------------------------------------------+
|:code:`scenarios` table column |:code:`project_lf_reserves_up_ba_scenario_id`   |
+-------------------------------+------------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_up`                       |
+-------------------------------+------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_lf_reserves_up_bas` |
+-------------------------------+------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_lf_reserves_up_bas`       |
+-------------------------------+------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+-------------------------------------------+
|:code:`scenarios` table column |:code:`lf_reserves_up_scenario_id`         |
+-------------------------------+-------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_up`                  |
+-------------------------------+-------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_lf_reserves_up` |
+-------------------------------+-------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_lf_reserves_up`       |
+-------------------------------+-------------------------------------------+

============================
Load-Following Reserves Down
============================

Balancing Areas
===============

Relevant tables:

+-------------------------------+----------------------------------------------------+
|:code:`scenarios` table column |:code:`lf_reserves_down_ba_scenario_id`             |
+-------------------------------+----------------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_down`                         |
+-------------------------------+----------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_lf_reserves_down_bas` |
+-------------------------------+----------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_lf_reserves_down_bas`       |
+-------------------------------+----------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+--------------------------------------------------+
|:code:`scenarios` table column |:code:`project_lf_reserves_down_ba_scenario_id`   |
+-------------------------------+--------------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_down`                       |
+-------------------------------+--------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_lf_reserves_down_bas` |
+-------------------------------+--------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_lf_reserves_down_bas`       |
+-------------------------------+--------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+---------------------------------------------+
|:code:`scenarios` table column |:code:`lf_reserves_down_scenario_id`         |
+-------------------------------+---------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_down`                  |
+-------------------------------+---------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_lf_reserves_down` |
+-------------------------------+---------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_lf_reserves_down`       |
+-------------------------------+---------------------------------------------+

===========================
Frequency Response Reserves
===========================

Balancing Areas
===============

Relevant tables:

+-------------------------------+------------------------------------------------------+
|:code:`scenarios` table column |:code:`frequency_response_ba_scenario_id`             |
+-------------------------------+------------------------------------------------------+
|:code:`scenario` table feature |:code:`of_frequency_response`                         |
+-------------------------------+------------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_frequency_response_bas` |
+-------------------------------+------------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_frequency_response_bas`       |
+-------------------------------+------------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+----------------------------------------------------+
|:code:`scenarios` table column |:code:`project_frequency_response_ba_scenario_id`   |
+-------------------------------+----------------------------------------------------+
|:code:`scenario` table feature |:code:`of_frequency_response`                       |
+-------------------------------+----------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_frequency_response_bas` |
+-------------------------------+----------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_frequency_response_bas`       |
+-------------------------------+----------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+-----------------------------------------------+
|:code:`scenarios` table column |:code:`frequency_response_scenario_id`         |
+-------------------------------+-----------------------------------------------+
|:code:`scenario` table feature |:code:`of_frequency_response`                  |
+-------------------------------+-----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_frequency_response` |
+-------------------------------+-----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_frequency_response`       |
+-------------------------------+-----------------------------------------------+

Policy (OPTIONAL)
*****************

===================================
Renewables Portfolio Standard (RPS)
===================================

Policy Zones
============

Relevant tables:

+-------------------------------+-----------------------------------------+
|:code:`scenarios` table column |:code:`rps_zone_scenario_id`             |
+-------------------------------+-----------------------------------------+
|:code:`scenario` table feature |:code:`of_rps`                           |
+-------------------------------+-----------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_rps_zones` |
+-------------------------------+-----------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_rps_zones`       |
+-------------------------------+-----------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+---------------------------------------+
|:code:`scenarios` table column |:code:`project_rps_zone_scenario_id`   |
+-------------------------------+---------------------------------------+
|:code:`scenario` table feature |:code:`of_rps`                         |
+-------------------------------+---------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_rps_zones` |
+-------------------------------+---------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_rps_zones`       |
+-------------------------------+---------------------------------------+

Target
======

Relevant tables:

+-------------------------------+--------------------------------+
|:code:`scenarios` table column |:code:`rps_scenario_id`         |
+-------------------------------+--------------------------------+
|:code:`scenario` table feature |:code:`of_rps`                  |
+-------------------------------+--------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_rps` |
+-------------------------------+--------------------------------+
|:code:`input_` tables          |:code:`inputs_system_rps`       |
+-------------------------------+--------------------------------+

==========
Carbon Cap
==========

Relevant tables:

+-------------------------------+------------------------------------------------+
|:code:`scenarios` table column |:code:`carbon_cap_zone_scenario_id`             |
+-------------------------------+------------------------------------------------+
|:code:`scenario` table feature |:code:`of_carbon_cap`                           |
+-------------------------------+------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_carbon_cap_zones` |
+-------------------------------+------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_carbon_cap_zones`       |
+-------------------------------+------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+----------------------------------------------+
|:code:`scenarios` table column |:code:`project_carbon_cap_zone_scenario_id`   |
+-------------------------------+----------------------------------------------+
|:code:`scenario` table feature |:code:`of_carbon_cap`                         |
+-------------------------------+----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_carbon_cap_zones` |
+-------------------------------+----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_carbon_cap_zones`       |
+-------------------------------+----------------------------------------------+

Target
======

Relevant tables:

+-------------------------------+---------------------------------------+
|:code:`scenarios` table column |:code:`carbon_cap_scenario_id`         |
+-------------------------------+---------------------------------------+
|:code:`scenario` table feature |:code:`of_carbon_cap`                  |
+-------------------------------+---------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_carbon_cap` |
+-------------------------------+---------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_carbon_cap`       |
+-------------------------------+---------------------------------------+
