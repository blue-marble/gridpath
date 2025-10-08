# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""

**Relevant tables:**

+---------------------------+-----------------------------------------------------+
|key column                 |:code:`hydro_operational_chars_scenario_id`          |
+---------------------------+-----------------------------------------------------+
|:code:`subscenario_` table |:code:`subscenarios_project_hydro_operational_chars` |
+---------------------------+-----------------------------------------------------+
|:code:`input_` table       |:code:`inputs_project_hydro_operational_chars`       |
+---------------------------+-----------------------------------------------------+

Hydro generators in GridPath require that average power, minimum power, and
maximum power be specified for the project for each *balancing
type*/*horizon* in which it can exist in a GridPath model. These inputs are in
the :code:`inputs_project_hydro_operational_chars`
for each project, balancing type, and horizon, while the names and
descriptions of the characteristis each project can be assigned are in the
:code:`subscenarios_project_hydro_operational_chars`. These two tables
are linked to each other and to the :code:`inputs_project_operational_chars`
via the :code:`hydro_operational_chars_scenario_id` key column. The
:code:`inputs_project_hydro_operational_chars` table can contain data
for projects and horizons that are not included in a particular GridPath
scenario: GridPath will select the subset of projects and horizons based
on the scenarios project portfolio and temporal subscenarios.

"""

if __name__ == "__main__":
    print(__doc__)
