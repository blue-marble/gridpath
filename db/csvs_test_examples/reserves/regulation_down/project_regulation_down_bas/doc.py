# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""

**Relevant tables:**

+-------------------------------+-------------------------------------------------+
|:code:`scenarios` table column |:code:`project_regulation_down_ba_scenario_id`   |
+-------------------------------+-------------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_down`                       |
+-------------------------------+-------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_regulation_down_bas` |
+-------------------------------+-------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_regulation_down_bas`       |
+-------------------------------+-------------------------------------------------+


One row per project and balancing area. A project may be mapped to several
balancing areas: it then splits its total provision among them in each
timepoint, and :code:`max_fraction_of_provision` caps the share of the total
that may go to each balancing area (blank = 1, i.e. no cap; the caps of a
project's balancing areas must sum to at least 1). Rows for balancing areas
not in the scenario's :code:`regulation_down_ba_scenario_id` are ignored.
"""

if __name__ == "__main__":
    print(__doc__)
