# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""

**Relevant tables:**

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_new_cost_scenario_id`          |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_new_cost`         |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_new_cost`               |
+--------------------------------+----------------------------------------------+

If the project portfolio includes projects of a 'new' capacity type
(:code:`gen_new_bin`, :code:`gen_new_lin`, :code:`stor_new_bin`, or
:code:`stor_new_lin`), the user must specify the cost for building a project
in each period and, optionally, any minimum and maximum requirements on the
total capacity to be build (see :ref:`new-project-potential-section-ref`).
Similarly to the specified-project tables, the primary key is the
combination of :code:`project_new_cost_scenario_id`, project, and period, so if
the user wanted the change the cost of just a single project for a single
period, all other project-period combinations would have to be re-inserted in
the database along with the new project_new_cost_scenario_id. Also note that
the :code:`inputs_project_new_cost` table can include projects that are not
in a particular scenario’s portfolio and periods that are not in the
scenario's temporal setup: each :code:`capacity_type` module has utilities
that pull the scenario data and only look at the portfolio selected by the
user, pull the projects with the 'new' *capacity types* from that list, and
then get the cost for only those projects and for the periods selected in
the temporal settings.

Note that capital costs must be annualized outside of GridPath and input as
$/MW-yr in the :code:`inputs_project_new_cost` table. For storage projects,
GridPath also requires an annualized cost for the project's energy
component, so both a $/MW-yr capacity component cost and a $/MWh-yr energy
component cost is required, allowing GridPath to endogenously determine
storage sizing.

"""
