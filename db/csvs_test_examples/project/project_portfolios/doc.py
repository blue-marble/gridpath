# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""
**Relevant tables:**

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_portfolio_scenario_id`         |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_portfolios`       |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_portfolios`             |
+--------------------------------+----------------------------------------------+

A scenario's 'project portfolio' determines which projects to include in a
scenario and how to treat each project’s capacity, e.g. is the capacity
going to be available to the optimization as 'given' (specified), will there
be decision variables associated with building capacity at this project, will
the optimization have the option to retire the project, etc. In GridPath,
this is called the project's *capacity_type* (see
:ref:`project-capacity-type-section-ref`). You can view all implemented
capacity types in the :code:`mod_capacity_types` table of the database.

The relevant database table is for the projet
portfolio data is :code:`inputs_project_portfolios`. The primary key of this
table is the :code:`project_portfolio_scenario_id` and the name of the
project. A new :code:`project_portfolio_scenario_id` is needed if the user
wants to select a different list of projects to be included in a scenario or
if she wants to keep the same list of projects but change a project’s capacity
type. In the latter case, all projects that don’t require a 'capacity type'
change would also have to be listed again in the database under the new
:code:`project_portfolio_scenario_id`. All
:code:`project_portfolio_scenario_id`'s along with their names and
descriptions must first be listed in the
:code:`subscenarios_project_portfolios` table.

"""
