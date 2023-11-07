# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""

**Relevant tables:**

+---------------------------+---------------------------------------------------------+
|key column                 |:code:`variable_generator_profile_scenario_id`           |
+---------------------------+---------------------------------------------------------+
|:code:`subscenario_` table |:code:`subscenarios_project_variable_generator_profiles` |
+---------------------------+---------------------------------------------------------+
|:code:`input_` table       |:code:`inputs_project_variable_generator_profiles`       |
+---------------------------+---------------------------------------------------------+

Variable generators in GridPath require a profile (power output as a fraction
of capacity) to be specified for the project for each *timepoint* in which
it can exist in a GridPath model. Profiles are in the
:code:`inputs_project_variable_generator_profiles`
for each variable project and timepoint, while the names and descriptions of
the profiles each project can be assigned are in the
:code:`subscenarios_project_variable_generator_profiles`. These two tables
are linked to each other and to the :code:`inputs_project_operational_chars`
via the :code:`variable_generator_profile_scenario_id` key column. The
:code:`inputs_project_variable_generator_profiles` table can contain data
for projects and timepoints that are not included in a particular GridPath
scenario: GridPath will select the subset of projects and timepoints based
on the scenarios project portfolio and temporal subscenarios.

"""

if __name__ == "__main__":
    print(__doc__)
