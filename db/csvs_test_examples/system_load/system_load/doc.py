# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""
**Relevant tables:**

+-------------------------------+---------------------------------+
|:code:`scenarios` table column |:code:`load_scenario_id`         |
+-------------------------------+---------------------------------+
|:code:`scenario` table feature |N/A                              |
+-------------------------------+---------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_load` |
+-------------------------------+---------------------------------+
|:code:`input_` tables          |:code:`inputs_system_load`       |
+-------------------------------+---------------------------------+

+-------------------------------+--------------------------------------------+
|:code:`scenarios` table column |:code:`load_components_scenario_id`         |
+-------------------------------+--------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_load_components` |
+-------------------------------+--------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_load_components`       |
+-------------------------------+--------------------------------------------+

+-------------------------------+----------------------------------------+
|:code:`scenarios` table column |:code:`load_levels_scenario_id`         |
+-------------------------------+----------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_load_levels` |
+-------------------------------+----------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_load_levels`       |
+-------------------------------+----------------------------------------+

The load to be used in a scenario must be specified in the
:code:`inputs_system_load` table under a :code:`load_scenario_id` key via two
subscenarios: :code:`load_components_scenario_id` and
:code:`load_levels_scenario_id`.

The :code:`load_components_scenario_id` determines which load components to
include for each load zone. In GridPath, the total static load is built up
from its components, e.g., the total static load can be the sum of a base
load profile and various electrification loads (EVs, building end uses, and so
on). The load profiles associated with each of those load components are
stored in the :code:`inputs_system_load_levels` table and are associated with a
:code:`load_levels_scenario_id`.

If the load for one load zone changes but not for others, all must be
included again under a different :code:`load_levels_scenario_id`. The
:code:`inputs_system_load_levels` table can contain data for load_zones and
timepoints not included in a scenario. GridPath will only select the load for
the relevant load zones and timepoints based on the
:code:`load_zone_scenario_id` and :code:`temporal_scenario_id` selected by the
user for the scenario in the :code:`scenarios` table.

"""
