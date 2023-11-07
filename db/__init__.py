# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
All tables names in the GridPath database start with one of seven prefixes:
:code:`mod_`, :code:`subscenario_`, :code:`inputs_`, :code:`scenarios`,
:code:`options_`, :code:`status_`, or :code:`ui_`. This structure is meant to
organize the tables by their function. Below are descriptions of each table
type and its role, and of the kind of data tables of this type contain.

***********************
The :code:`mod_` Tables
***********************
The :code:`mod_` should not be modified except by developers. These contain
various data used by the GridPath platform to describe available
functionality, help enforce input data consistency and integrity, and aid in
validation.

***************************************************
The :code:`subscenario_` and :code:`inputs_` Tables
***************************************************
Most tables in the GridPath database have the :code:`subscenario_` and
:code:`inputs_` prefix. With a few exceptions, for each :code:`subscenario_`
table, there is a respective :code:`inputs_` table (i.e. the tables have the
same name except for the prefix). This is because the :code:`subscenario_`
tables contain the descriptions of the input data contained in the
:code:`inputs_` tables. For example the :code:`inputs_system_load` may
contain three different load profiles -- low, mid, and high; the
:code:`subscenarios_system_load` will then contain three rows, one for each
load profile, with its description and ID. The pairs of :code:`subscenario_`
and :code:`inputs_` are linked via an ID column: in the case of the system
load tables, that is the :code:`load_scenario_id` column. We call these
shared table keys *subscenario IDs*, as we use them to create a full
GridPath scenario in the :code:`scenarios` table.

***************************
The :code:`scenarios` Table
***************************
In GridPath, we use the term 'scenario' to describe a model run with a
particular set of inputs. Some of those inputs stay the same from scenario to
scenario and others we vary to understand their effect on the results. For
example, we could keep some input types like the zonal and transmission
topography, temporal resolution, resource availability, and policy
requirements the same across scenarios, but vary other input types, e.g. the
load profile, the cost of solar, and the operational characteristics of coal,
to create different scenarios. We call each of those inputs types a
'subscenario' since they are the building blocks of a full scenario. In
GridPath, you can create a scenario by populating a row of the
:code:`scenarios` table. The columns of the :code:`scenarios` table are
linked one of the 'building blocks' -- the data in :code:`inputs_` tables --
via the respective *subscenario ID*.

For example, the :code:`load_scenario_id` column of the :code:`scenarios` table
references the :code:`load_scenario_id` column of the
:code:`subscenarios_system_load` table, which in turn determines which load
profile contained in the :code:`inputs_system_load` table the scenario
should use. In our example with three different load profiles, the data for
which are contained in the :code:`inputs_system_load` table,
:code:`subscenarios_system_load` will contain three rows with values of 1,
2, and 3 respectively in the :code:`load_scenario_id` column; in the
:code:`scenarios` table, the user would then be able to select a value of 1,
2, or 3 in the :code:`load_scenario_id` column to determine which load
profile the scenario should use. Similarly, we would select the solar costs
to use in the scenario via the :code:`projects_new_cost_scenario_id` column
of the :code:`scenarios` table (which is linked to the
:code:`subscenarios_project_new_cost` and :code:`inputs_project_new_cost`
tables) and the operational characteristics of coal to use via the
:code:`project_operational_chars_scenario_id` column (which is linked to the
:code:`subscenarios_project_operational_chars` and
:code:`inputs_project_operational_chars` tables).

***************************
The :code:`options_` Tables
***************************
Some GridPath run options can be specified via the database in the
:code:`options_` tables. Currently, this includes the solver options that
can be specified for a scenario run

**************************
The :code:`status_` Tables
**************************
GridPath keeps track of scenario validation and run status. The scenario
status is recorded in the :code:`scenarios` table (in the
:code:`validation_status_id` and :code:`run_status_id` columns) and an
additional detail can be found in the :code:`status_` tables. Currently,
this includes a single table: the :code:`status_validation` table, which
contains information about errors encountered during validation for each
scenario that has been validated.

**********************
The :code:`ui_` Tables
**********************
The :code:`ui_` tables are used to include and exclude components of the
GridPath user interface.

***********************
The :code:`viz_` Tables
***********************
The :code:`viz_` tables are used in the GridPath visualization suite, for
instance when determining in which color and order to plot the technologies in
the dispatch plot.


"""
