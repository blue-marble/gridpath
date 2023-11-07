# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""

**Relevant tables:**

+--------------------------------+--------------------------------------------------+
|:code:`scenarios` table column  |:code:`project_specified_fixed_cost_scenario_id`  |
+--------------------------------+--------------------------------------------------+
|:code:`scenarios` table feature |N/A                                               |
+--------------------------------+--------------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_specified_fixed_cost` |
+--------------------------------+--------------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_specified_fixed_cost`       |
+--------------------------------+--------------------------------------------------+

If the project portfolio includes project of the capacity types
:code:`gen_spec`, :code:`gen_ret_bin`, :code:`gen_ret_lin`, or
:code:`stor_spec`, the user must select the fixed O&M costs associated with
the specified project capacity in every period. These can be varied by
scenario via the :code:`project_specified_fixed_cost_scenario_id` subscenario.

The treatment for specified project fixed cost inputs is similar to that for
their capacity (see :ref:`specified-project-capacity-section-ref`).

"""

if __name__ == "__main__":
    print(__doc__)
