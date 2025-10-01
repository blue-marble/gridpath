# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""

**Relevant tables:**

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_new_potential_scenario_id`     |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_new_potential`    |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_new_potential`          |
+--------------------------------+----------------------------------------------+

If the project portfolio includes projects of a 'new' capacity type
(:code:`gen_new_bin`, :code:`gen_new_lin`, :code:`stor_new_bin`, or
:code:`stor_new_lin`), the user may specify the minimum and maximum
cumulative new capacity to be built in each period in the
:code:`inputs_project_new_potential` table. For storage project, the minimum
and maximum energy capacity may also be specified. All columns are optional
and NULL values are interpreted by GridPath as no constraint. Projects that
don't either a minimum or maximum cumulative new capacity constraints can be
omitted from this table completely.

"""
