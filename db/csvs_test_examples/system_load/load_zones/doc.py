# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""
**Relevant tables:**

+-------------------------------+----------------------------------------------+
|:code:`scenarios` table column |:code:`load_zone_scenario_id`                 |
+-------------------------------+----------------------------------------------+
|:code:`scenario` table feature |N/A                                           |
+-------------------------------+----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_load_zones`     |
+-------------------------------+----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_load_zones`           |
+-------------------------------+----------------------------------------------+

The :code:`subscenarios_geography_load_zones` contains the IDs, names, and
descriptions of the load zone scenarios to be available to the user. This
table must be populated before data for the respective
:code:`load_zone_scenario_id` can be imported into the input table.

The user must decide the load zones will be, i.e. what is the unit at which
load is met. There are some parameters associated with each load zone,
e.g. unserved-energy and overgeneration penalties. The relevant database
table is :code:`inputs_geography_load_zones` where the user must list the
load zones along with whether unserved energy and overgeneration should be
allowed in the load zone, and what the violation penalties would be. If a
user wanted to create a different 'geography,' e.g. combine load zones, add
a load zone, remove one, have a completely different set of load zones, etc.,
they would need to create a new :code:`load_zone_scenario_id` and list the
load zones. If a user wanted to keep the same load zones, but change the
unserved energy or overgeneration penalties, they would also need to create
a new :code:`load_zone_scenario_id`.

Separately, each generator to be included in a scenario must be assigned a
load zone to whose load-balance constraint it can contribute
(see :ref:`project-geography-section-ref`).

GridPath also includes other geographic layers, including those for
operating reserves, reliability reserves, and policy requirements.

A scenario's load zone geographic setup is selected via the
:code:`load_zone_scenario_id` column of the :code:`scenarios` table.


"""
