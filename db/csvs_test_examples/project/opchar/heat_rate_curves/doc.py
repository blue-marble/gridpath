# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""

**Relevant tables:**

+---------------------------+----------------------------------------------+
|key column                 |:code:`heat_rate_curves_scenario_id`          |
+---------------------------+----------------------------------------------+
|:code:`subscenario_` table |:code:`subscenarios_project_heat_rate_curves` |
+---------------------------+----------------------------------------------+
|:code:`input_` table       |:code:`inputs_project_heat_rate_curves`       |
+---------------------------+----------------------------------------------+

Fuel-based generators in GridPath require a heat-rate curve to be specified
for the project. Heat rate curves are modeled via piecewise linear
constraints and must be input in terms of an average heat rate for a load
point. These data are in the :code:`inputs_project_heat_rate_curves` for
each project that requires a heat rate, while the names and descriptions of
the heat rate curves each project can be assigned are in the
:code:`subscenarios_project_heat_rate_curves`. These two tables are linked
to each other and to the :code:`inputs_project_operational_chars` via the
:code:`heat_rate_curves_scenario_id` key column. The inputs table can contain
data for projects that are not included in a GridPath scenario, as the
relevant projects for a scenario will be pulled based on the scenario's
project portfolio subscenario.

"""

if __name__ == "__main__":
    print(__doc__)
