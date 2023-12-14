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

The load for each load zone must be specified the :code:`inputs_system_load`
table under a :code:`load_scenario_id` key. If the load for one load zone
changes but not for others, all must be included again under a different
:code:`load_scenario_id`. The :code:`inputs_system_load` table can contain
data for timepoints not included in a scenario. GridPath will only select
the load for the relevant timepoints based on the
:code:`temporal_scenario_id` selected by the user in the :code:`scenarios`
table.

"""
