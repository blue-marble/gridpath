# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""
**Relevant tables:**

+-------------------------------+----------------------------------------+
|:code:`scenarios` table column |:code:`project_load_zone_scenario_id`   |
+-------------------------------+----------------------------------------+
|:code:`scenario` table feature |N/A                                     |
+-------------------------------+----------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_load_zones` |
+-------------------------------+----------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_load_zones`       |
+-------------------------------+----------------------------------------+

Each *project* in a GridPath scenario must be assigned a load zone to whose
load-balance constraint it will contribute. In the
:code:`inputs_project_load_zones`, each
:code:`project_load_zone_scenario_id` should list all projects with their load
zones. For example, if a user initially had three load zones and assigned
one of them to each project, then decided to combine two of those load
zones into one, they would need to create a new
:code:`project_load_zone_scenario_id` that includes all projects from the
two combined zones with the new zone assigned to them as well as all
projects from the zone that was not modified. This
:code:`inputs_project_load_zones` table can include more projects that are
modeled in a scenario, as GridPath will select only the subset of projects
from the scenario's project portfolio (see
:ref:`project-portfolio-section-ref`).

"""
