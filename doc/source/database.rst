.. _database-section-ref:

########
Database
########

Table chapter describes the following:

* :ref:`database-structure-section-ref` : the structure of the database and its
  associated tables
* :ref:`building-the-database-section-ref` : instructions on how to build the
  database
* :ref:`database-testing-section-ref` : instructions on how to validate the
  database inputs


.. _database-structure-section-ref:

******************
Database Structure
******************

All tables names in the GridPath database start with one of seven prefixes:
:code:`mod_`, :code:`subscenario_`, :code:`inputs_`, :code:`scenarios`,
:code:`options_`, :code:`status_`, or :code:`ui_`. This structure is meant to
organize the tables by their function. Below are descriptions of each table
type and its role, and of the kind of data tables of this type contain.

The :code:`mod_` Tables
***********************
The :code:`mod_` should not be modified except by developers. These contain
various data used by the GridPath platform to describe available
functionality, help enforce input data consistency and integrity, and aid in
validation.


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

The :code:`options_` Tables
***************************
Some GridPath run options can be specified via the database in the
:code:`options_` tables. Currently, this includes the solver options that
can be specified for a scenario run

The :code:`status_` Tables
**************************
GridPath keeps track of scenario validation and run status. The scenario
status is recorded in the :code:`scenarios` table (in the
:code:`validation_status_id` and :code:`run_status_id` columns) and an
additional detail can be found in the :code:`status_` tables. Currently,
this includes a single table: the :code:`status_validation` table, which
contains information about errors encountered during validation for each
scenario that has been validated.

The :code:`ui_` Tables
**********************
The :code:`ui_` tables are used to include and exclude components of the
GridPath user interface.

The :code:`viz_` Tables
**********************
The :code:`viz_` tables are used in the GridPath visualization suite, for
instance when determining in which color and order to plot the technologies in
the dispatch plot.

.. _building-the-database-section-ref:

*********************
Building the Database
*********************

.. note:: We'll be expanding this section considerably in the next few weeks.

Temporal Inputs
***************

**Relevant tables:**

+-------------------------------+----------------------------------------------+
|:code:`scenarios` table column |:code:`temporal_scenario_id`                  |
+-------------------------------+----------------------------------------------+
|:code:`scenario` table feature |N/A                                           |
+-------------------------------+----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_temporal_timepoints`      |
+-------------------------------+----------------------------------------------+
|:code:`input_` tables          |- :code:`inputs_temporal_timepoints`          |
|                               |- :code:`inputs_temporal_horizons`            |
|                               |- :code:`inputs_temporal_horizon_timepoints`  |
|                               |- :code:`inputs_temporal_periods`             |
|                               |- :code:`inputs_temporal_subproblems`         |
|                               |- :code:`inputs_temporal_subproblem_stages`   |
+-------------------------------+----------------------------------------------+

The first step in building the GridPath database is to determine the
temporal span and resolution of the scenarios to be run. See the
:ref:`temporal-setup-section-ref` for a detailed description of the types
of temporal inputs in GridPath.

The user must decide on temporal resolution and span, i.e. timepoints
(e.g. hourly, 4-hourly, 15-minute, etc.) and how the *timepoints* are
connected to each other in an optimization: 1) what the *horizon(s)* is (are),
e.g. we can see as far ahead as one day, one week, or a full 8760 in making
operational decisions and 2) what *period* a timepoint belongs to, with a
period being the time when investment decisions are made, so depending on a
period a different set of resources is available in a particular timepoint. 
In addition, the user has to specify whether all timepoints are optimized 
concurrently, or if they are split into *subproblems* (e.g. the full year is
solved a week at a time in a production-cost scenario). Finally, the 
temporal inputs also define whether the scenario will have *stages*, i.e. 
whether some results from one stage will be fixed and fed into a subsequent 
stage with some inputs also potentially changed.

The subscenarios table has the :code:`temporal_scenario_id` column as its
primary key. This ID refers to a particular set of *timepoints* and how they
are linked into *horizons*, *periods*, *subproblems*, and *stages*. For
example, we could be running production cost for 2020 (the *period* simply a
year in this case with no investment decisions), but optimize each day
individually in one scenario (the *subproblem* is the day) and a week at a
time in another scenario (the *subproblem* is a week). We have the same
timepoints in both of those scenarios but they are linked differently into
*subproblems*, so these will be two different :code:`temporal_scenario_id`’s.
Another example might be to use the same sample of “representative” days to
optimize investment and dispatch between 2021 and 2050, but group the days
depending on what year they belong to (30 *periods* = higher resolution on
investment decisions) in one scenario and what decade they belong to in
another scenario (3 *periods* = lower resolution on investment decisions). In
this case we would have the same timepoints and horizons (as well as a single
subproblem and a single stage), but they would be grouped differently into
periods, so, again, we’d need two different :code:`temporal_scenario_id`’s.

Descriptions of the relevant tables are below:

The :code:`subscenarios_temporal_timepoints` contains the IDs, names, and
descriptions of the temporal scenarios to be available to the user. This
table must be populated before data for the respective
:code:`temporal_scenario_id` can be imported into the input tables.

The :code:`inputs_temporal_timepoints`: for a given temporal scenario, the
timepoints along with their horizon and period as well as the “resolution”
of each timepoint (is it an hour, a 4-hour chunk, 15-minute chunk, etc.)

The :code:`inputs_temporal_subproblems` tables contains the subproblems for
each :code:`temporal_scenario_id` (usually used in production-cost modeling,
set to 1 in capacity-expansion scenarios with a single subproblem).

The :code:`inputs_temporal_subproblems_stages` table contains the information
about whether there are stages within each subproblem. Stages must be given
an ID and can optionally be given a name.

The :code:`inputs_temporal_periods` table contains the information about the
investment periods in the respective :code:`temporal_scenario_id` along with
the data for the discount factor to be applied to the period and the number of
years it represents (e.g. we can use 2030 to represent the 10-year period
between 2025 and 2034).

The :code:`inputs_temporal_horizons` table contains information about the
*horizons* within a :code:`temporal_scenario_id` along their balancing type,
period, and boundary ('circular' if the last timepoint of the horizon is
used as the previous timepoint for the first timepoint of the horizon and
'linear' if we ignore the previous timepoint for the first timepoint of the
horizon).

The :code:`inputs_temporal_timepoints` table contains information about the
timepoints within each :code:`temporal_scenario_id`, :code:`subproblem_id`, and
:code:`stage_id`, including the period of the timepoint, its 'resolution' (the
number of hours in the timepoint), its weight (the number of timepoints not
explicitly modeled that this timepoint represents), the ID of the timepoint
from the previous stage that this timepoint maps to (if any), whether this
timepoint is part of a spinup or lookahead, the month of this timepoint, and
the hour of day of this timepoint.

The :code:`inputs_temporal_horizon_timepoints` table describes how timeponts
are organized into horizons for each temporal_scenario_id, subproblem_id, and
stage_id. A timepoint can belong to more than one horizon if those horizons
are of different balancing types (e.g. the same horizon can belong to a
'day' horizon, a 'week' horizon, a 'month' horizons, and a 'year' horizon).

A scenario's temporal setup is selected via the :code:`temporal_scenario_id`
column of the :code:`scenarios` table.



Load Zone Inputs
****************

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

System Load
***********

**Relevant tables:**

+-------------------------------+---------------------------------+
|:code:`scenarios` table column |:code:`load_scenario_id`         |
+-------------------------------+---------------------------------+
|:code:`scenario` table feature |N/A                              |
+-------------------------------+---------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_load` |
+-------------------------------+---------------------------------+
|:code:`input_` tables          |:code:`inputs_system_load`       |
+-------------------------------+---------------------------------+

The load for each load zone must be specified the :code:`inputs_system_load`
table under a :code:`load_scenario_id` key. If the load for one load zone
changes but not for others, all must be included again under a different
:code:`load_scenario_id`. The :code:`inputs_system_load` table can contain
data for timepoints not included in a scenario. GridPath will only select
the load for the relevant timepoints based on the
:code:`temporal_scenario_id` selected by the user in the :code:`scenarios`
table.

Project Inputs
**************

Generator and storage resources in GridPath are called *projects*. Each
project can be assigned different characteristics depending on the scenario,
whether its geographic location, ability to contribute to reserve or policy
requirements, its capacity and operating characteristics. You can optionally
import all projects that may be part of a scenario in the
:code:`inputs_project_all` table of the GridPath database.

.. _project-geography-section-ref:

=================
Project Geography
=================

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


.. _project-portfolio-section-ref:

=================
Project Portfolio
=================

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


==================
Specified Projects
==================

.. _specified-project-capacity-section-ref:

Capacity
========

**Relevant tables:**

+--------------------------------+------------------------------------------------+
|:code:`scenarios` table column  |:code:`project_specified_capacity_scenario_id`  |
+--------------------------------+------------------------------------------------+
|:code:`scenarios` table feature |N/A                                             |
+--------------------------------+------------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_specified_capacity` |
+--------------------------------+------------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_specified_capacity`       |
+--------------------------------+------------------------------------------------+

If the project portfolio includes project of the capacity types
:code:`gen_spec`, :code:`gen_ret_bin`, :code:`gen_ret_lin`, or
:code:`stor_spec`, the user must select that amount of project capacity that
the optimization should see as given (i.e. specified) in every period as
well as the associated fixed O&M costs (see
:ref:`specified-project-fixed-cost-section-ref`). Project
capacities are in the :code:`inputs_project_specified_capacity` table. For
:code:`gen_` capacity types, this table contains the project's power rating
and for :code:`stor_spec` it also contains the storage project's energy rating.

The primary key of this table includes the
:code:`project_specified_capacity_scenario_id`, the project name, and the
period. Note that this table can include projects that are not in the
user’s portfolio: the utilities that pull the scenario data look at the
scenario’s portfolio, pull the projects with the “specified” capacity types
from that, and then get the capacity for only those projects (and for the
periods selected based on the scenario's temporal setting). A new
:code:`project_specified_capacity_scenario_id` would be needed if a user wanted
to change the available capacity of even only a single project in a single
period (and all other project-year-capacity data points would need to be
re-inserted in the table under the new
:code:`project_specified_capacity_scenario_id`).

.. _specified-project-fixed-cost-section-ref:

Fixed Costs
===========

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

============
New Projects
============

Capital Costs
=============

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
$/kW-yr in the :code:`inputs_project_new_cost` table. For storage projects,
GridPath also requires an annualized cost for the project's energy
component, so both a $/kW-yr capacity component cost and a $/kWh-yr energy
component cost is required, allowing GridPath to endogenously determine
storage sizing.

.. _new-project-potential-section-ref:

Potential
=========

**Relevant tables:**

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_new_potential_scenario_id`     |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_new_potential`    |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_new_potential`          |
+--------------------------------+----------------------------------------------+

If the project portfolio includes projects of a 'new' capacity type
(:code:`gen_new_bin`, :code:`gen_new_lin`, :code:`stor_new_bin`, or
:code:`stor_new_lin`), the user may specify the minimum and maximum
cumulative new capacity to be built in each period in the
:code:`inputs_project_new_potential` table. For storage project, the minimum
and maximum energy capacity may also be specified. All columns are optional
and NULL values are interpreted by GridPath as no constraint. Projects that
don't either a minimum or maximum cumulative new capacity constraints can be
omitted from this table completely.

====================
Project Availability
====================

**Relevant tables:**

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_availability_scenario_id`      |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |N/A                                           |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_availability`     |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_availability_types`     |
+--------------------------------+----------------------------------------------+

All projects in a GridPath scenario must be a assigned an *availability
type*, which determines whether their capacity is operational in each
timepoint in which the capacity exists. All implemented availability types are
listed in the :code:`mod_availability_types` table.

Each project's availability type are given in the
:code:`inputs_project_availability_types`. The availability types currently
implemented include :code:`exogenous` (availability is determined outside of
a GridPath model via the data fed into it) and two endogenous types:
:code:`binary` and :code:`continuous` that require certain inputs that
determine how availability is constrained in the GridPath model. See the
:ref:`project-availability-type-section-ref` section for more info. In
addition to the project availability types, the
:code:`inputs_project_availability_types` table contains the information for
how to find any additional data needed to determine project availability with
the :code:`exogenous_availability_scenario_id` and
:code:`endogenous_availability_scenario` columns for the endogenous and
exogenous types respectively. The IDs in the former column are linked to the
data in the :code:`inputs_project_availability_exogenous` table and in the
latter column to the :code:`inputs_project_availability_endogenous` table.
For projects of the :code:`exogenous` availability type, if the value is in the
:code:`exogenous_availability_scenario_id` column is NULL, no availability
capacity derate is applied by GridPath. For projects of a :code:`binary` of
:code:`continuous` availability type, a value in the
:code:`endogenous_availability_scenario_id` is required.

Exogenous
=========

**Relevant tables:**

+---------------------------+----------------------------------------------------+
|:code:`subscenario_` table |:code:`subscenarios_project_availability_exogenous` |
+---------------------------+----------------------------------------------------+
|:code:`input_` table       |:code:`inputs_project_availability_exogenous`       |
+---------------------------+----------------------------------------------------+

Within each :code:`project_availability_scenario_id`, a project of the
:code:`exogenous` *availability type* can point to a particular
:code:`exogenous_availability_scenario_id`, the data for which is contained
in the :code:`inputs_project_availability_exogenous` table. The names and
descriptions of each :code:`project` and
:code:`exogenous_availability_scenario_id` combination are in the
:code:`subscenarios_project_availability_exogenous` table. The availability
derate for each combination is defined by stage and timepoint, and must be
between 0 (full derate) and 1 (no derate).

Endogenous
==========

**Relevant tables:**

+---------------------------+-----------------------------------------------------+
|:code:`subscenario_` table |:code:`subscenarios_project_availability_endogenous` |
+---------------------------+-----------------------------------------------------+
|:code:`input_` table       |:code:`inputs_project_availability_endogenous`       |
+---------------------------+-----------------------------------------------------+

Within each :code:`project_availability_scenario_id`, a project of the
:code:`binary` or :code:`continuous` *availability type* must point to a
particular :code:`endogenous_availability_scenario_id`, the data for which
is contained in the :code:`inputs_project_availability_endogenous` table. The
names and descriptions of each :code:`project` and
:code:`endogenous_availability_scenario_id` combination are in the
:code:`subscenarios_project_availability_endogenous` table. For each
combination, the user must define to the total number of hours that a
project will be unavailable per period, the minimum and maximum length of
each unavailability event in hours, and the minimum and maximum number of
hours between unavailability events. Based on these inputs, GridPath determines
the exact availability schedule endogenously.

===================================
Project Operational Characteristics
===================================

**Relevant tables:**

+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_operational_chars_scenario_id`  |
+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table feature |N/A                                            |
+--------------------------------+-----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_operational_chars` |
+--------------------------------+-----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_operational_chars`       |
+--------------------------------+-----------------------------------------------+

The user must decide how to model the operations of *projects*, e.g. is this
a fuel-based dispatchable (CCGT) or baseload project (nuclear), is it an
intermittent plant, is it a battery, etc. In GridPath, this is called the
project’s *operational type*. All implemented operational types are listed
in the :code:`mod_operational_types` table.

Each *operational type* has an associated set of characteristics, which must
be included in the :code:`inputs_project_operational_chars` table. The primary
key of this table is the :code:`project_operational_chars_scenario_id`,
which is also the column that determines project operational characteristics
for a scenario via the :code:`scenarios` table, and the project. If a
project’s operational type changes (e.g. the user decides to model a coal
plant as, say, :code:`gen_always_on` instead of :code:`gen_commit_bin`) or the
user wants to modify one of its operating characteristics (e.g. its minimum
loading level), then a new :code:`project_operational_chars_scenario_id` must
be created and all projects listed again, even if the rest of the projects'
operating types and characteristics do not change.

The ability to provide each type of reserve is currently an 'operating
characteristic' determined via the :code:`inputs_project_operational_chars`
table.

Not all operational types have all the characteristics in
the :code:`inputs_project_operational_chars`. GridPath's validation suite
does check whether certain required characteristic for an operational type are
populated and warns the user if some characteristics that have been filled
are actually not used by the respective operational type. We will list
required and optional characteristics for each operational type in this
section soon.

Several types of operational characteristics vary by dimensions are other
than project, so they are input in separate tables and linked to the
:code:`inputs_project_operational_chars` via an ID column. These include
heat rates, variable generator profiles, and hydro characteristics.

Heat Rates (OPTIONAL)
=====================

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

Variable Generator Profiles (OPTIONAL)
======================================

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

Hydro Operational Characteristics (OPTIONAL)
============================================

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

Transmission Inputs (OPTIONAL)
******************************

Optional inputs needed if transmission feature is enabled for a scenario.

======================
Transmission Portfolio
======================

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_portfolio_scenario_id`         |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                       |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_portfolios`  |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_portfolios`        |
+--------------------------------+----------------------------------------------+

=======================
Transmission Topography
=======================

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_load_zones_scenario_id`   |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                       |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_load_zones`  |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_load_zones`        |
+--------------------------------+----------------------------------------------+

======================
Specified Transmission
======================

Capacity
========

Relevant tables:

+--------------------------------+----------------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_specified_capacity_scenario_id`  |
+--------------------------------+----------------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                             |
+--------------------------------+----------------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_specified_capacity` |
+--------------------------------+----------------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_specified_capacity`       |
+--------------------------------+----------------------------------------------------+


================
New Transmission
================

Capital Costs
=============

Relevant tables:

+--------------------------------+----------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_new_cost_scenario_id`     |
+--------------------------------+----------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                       |
+--------------------------------+----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_new_cost`    |
+--------------------------------+----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_new_cost`          |
+--------------------------------+----------------------------------------------+

========================================
Transmission Operational Characteristics
========================================

+--------------------------------+----------------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_operational_chars_scenario_id`  |
+--------------------------------+----------------------------------------------------+
|:code:`scenarios` table feature |:code:`of_transmission`                             |
+--------------------------------+----------------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_operational_chars` |
+--------------------------------+----------------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_operational_chars`       |
+--------------------------------+----------------------------------------------------+


Fuel Inputs (OPTIONAL)
**********************

====================
Fuel Characteristics
====================

Relevant tables:

+--------------------------------+-----------------------------------+
|:code:`scenarios` table column  |:code:`fuel_scenario_id`           |
+--------------------------------+-----------------------------------+
|:code:`scenarios` table feature |:code:`of_fuels`                   |
+--------------------------------+-----------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_fuels` |
+--------------------------------+-----------------------------------+
|:code:`input_` tables           |:code:`inputs_project_fuels`       |
+--------------------------------+-----------------------------------+

===========
Fuel Prices
===========

Relevant tables:

+--------------------------------+-----------------------------------------+
|:code:`scenarios` table column  |:code:`fuel_price_scenario_id`           |
+--------------------------------+-----------------------------------------+
|:code:`scenarios` table feature |:code:`of_fuels`                         |
+--------------------------------+-----------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_fuel_prices` |
+--------------------------------+-----------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_fuel_prices`       |
+--------------------------------+-----------------------------------------+


Reserves (OPTIONAL)
*******************

=============
Regulation Up
=============

Balancing Areas
===============

Relevant tables:

+-------------------------------+-------------------------------------------------+
|:code:`scenarios` table column |:code:`regulation_up_ba_scenario_id`             |
+-------------------------------+-------------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_up`                         |
+-------------------------------+-------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_regulation_up_bas` |
+-------------------------------+-------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_regulation_up_bas`       |
+-------------------------------+-------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+-----------------------------------------------+
|:code:`scenarios` table column |:code:`project_regulation_up_ba_scenario_id`   |
+-------------------------------+-----------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_up`                       |
+-------------------------------+-----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_regulation_up_bas` |
+-------------------------------+-----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_regulation_up_bas`       |
+-------------------------------+-----------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+------------------------------------------+
|:code:`scenarios` table column |:code:`regulation_up_scenario_id`         |
+-------------------------------+------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_up`                  |
+-------------------------------+------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_regulation_up` |
+-------------------------------+------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_regulation_up`       |
+-------------------------------+------------------------------------------+

===============
Regulation Down
===============

Balancing Areas
===============

Relevant tables:

+-------------------------------+---------------------------------------------------+
|:code:`scenarios` table column |:code:`regulation_down_ba_scenario_id`             |
+-------------------------------+---------------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_down`                         |
+-------------------------------+---------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_regulation_down_bas` |
+-------------------------------+---------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_regulation_down_bas`       |
+-------------------------------+---------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+-------------------------------------------------+
|:code:`scenarios` table column |:code:`project_regulation_down_ba_scenario_id`   |
+-------------------------------+-------------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_down`                       |
+-------------------------------+-------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_regulation_down_bas` |
+-------------------------------+-------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_regulation_down_bas`       |
+-------------------------------+-------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+--------------------------------------------+
|:code:`scenarios` table column |:code:`regulation_down_scenario_id`         |
+-------------------------------+--------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_down`                  |
+-------------------------------+--------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_regulation_down` |
+-------------------------------+--------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_regulation_down`       |
+-------------------------------+--------------------------------------------+

=================
Spinning Reserves
=================

Balancing Areas
===============

Relevant tables:

+-------------------------------+-----------------------------------------------------+
|:code:`scenarios` table column |:code:`spinning_reserves_ba_scenario_id`             |
+-------------------------------+-----------------------------------------------------+
|:code:`scenario` table feature |:code:`of_spinning_reserves`                         |
+-------------------------------+-----------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_spinning_reserves_bas` |
+-------------------------------+-----------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_spinning_reserves_bas`       |
+-------------------------------+-----------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+---------------------------------------------------+
|:code:`scenarios` table column |:code:`project_spinning_reserves_ba_scenario_id`   |
+-------------------------------+---------------------------------------------------+
|:code:`scenario` table feature |:code:`of_spinning_reserves`                       |
+-------------------------------+---------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_spinning_reserves_bas` |
+-------------------------------+---------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_spinning_reserves_bas`       |
+-------------------------------+---------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+----------------------------------------------+
|:code:`scenarios` table column |:code:`spinning_reserves_scenario_id`         |
+-------------------------------+----------------------------------------------+
|:code:`scenario` table feature |:code:`of_spinning_reserves`                  |
+-------------------------------+----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_spinning_reserves` |
+-------------------------------+----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_spinning_reserves`       |
+-------------------------------+----------------------------------------------+

==========================
Load-Following Reserves Up
==========================

Balancing Areas
===============

Relevant tables:

+-------------------------------+--------------------------------------------------+
|:code:`scenarios` table column |:code:`lf_reserves_up_ba_scenario_id`             |
+-------------------------------+--------------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_up`                         |
+-------------------------------+--------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_lf_reserves_up_bas` |
+-------------------------------+--------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_lf_reserves_up_bas`       |
+-------------------------------+--------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+------------------------------------------------+
|:code:`scenarios` table column |:code:`project_lf_reserves_up_ba_scenario_id`   |
+-------------------------------+------------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_up`                       |
+-------------------------------+------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_lf_reserves_up_bas` |
+-------------------------------+------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_lf_reserves_up_bas`       |
+-------------------------------+------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+-------------------------------------------+
|:code:`scenarios` table column |:code:`lf_reserves_up_scenario_id`         |
+-------------------------------+-------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_up`                  |
+-------------------------------+-------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_lf_reserves_up` |
+-------------------------------+-------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_lf_reserves_up`       |
+-------------------------------+-------------------------------------------+

============================
Load-Following Reserves Down
============================

Balancing Areas
===============

Relevant tables:

+-------------------------------+----------------------------------------------------+
|:code:`scenarios` table column |:code:`lf_reserves_down_ba_scenario_id`             |
+-------------------------------+----------------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_down`                         |
+-------------------------------+----------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_lf_reserves_down_bas` |
+-------------------------------+----------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_lf_reserves_down_bas`       |
+-------------------------------+----------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+--------------------------------------------------+
|:code:`scenarios` table column |:code:`project_lf_reserves_down_ba_scenario_id`   |
+-------------------------------+--------------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_down`                       |
+-------------------------------+--------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_lf_reserves_down_bas` |
+-------------------------------+--------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_lf_reserves_down_bas`       |
+-------------------------------+--------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+---------------------------------------------+
|:code:`scenarios` table column |:code:`lf_reserves_down_scenario_id`         |
+-------------------------------+---------------------------------------------+
|:code:`scenario` table feature |:code:`of_lf_reserves_down`                  |
+-------------------------------+---------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_lf_reserves_down` |
+-------------------------------+---------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_lf_reserves_down`       |
+-------------------------------+---------------------------------------------+

===========================
Frequency Response Reserves
===========================

Balancing Areas
===============

Relevant tables:

+-------------------------------+------------------------------------------------------+
|:code:`scenarios` table column |:code:`frequency_response_ba_scenario_id`             |
+-------------------------------+------------------------------------------------------+
|:code:`scenario` table feature |:code:`of_frequency_response`                         |
+-------------------------------+------------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_frequency_response_bas` |
+-------------------------------+------------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_frequency_response_bas`       |
+-------------------------------+------------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+----------------------------------------------------+
|:code:`scenarios` table column |:code:`project_frequency_response_ba_scenario_id`   |
+-------------------------------+----------------------------------------------------+
|:code:`scenario` table feature |:code:`of_frequency_response`                       |
+-------------------------------+----------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_frequency_response_bas` |
+-------------------------------+----------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_frequency_response_bas`       |
+-------------------------------+----------------------------------------------------+

Requirement
===========

Relevant tables:

+-------------------------------+-----------------------------------------------+
|:code:`scenarios` table column |:code:`frequency_response_scenario_id`         |
+-------------------------------+-----------------------------------------------+
|:code:`scenario` table feature |:code:`of_frequency_response`                  |
+-------------------------------+-----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_frequency_response` |
+-------------------------------+-----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_frequency_response`       |
+-------------------------------+-----------------------------------------------+

Policy (OPTIONAL)
*****************

===================================
Renewables Portfolio Standard (RPS)
===================================

Policy Zones
============

Relevant tables:

+-------------------------------+-----------------------------------------+
|:code:`scenarios` table column |:code:`rps_zone_scenario_id`             |
+-------------------------------+-----------------------------------------+
|:code:`scenario` table feature |:code:`of_rps`                           |
+-------------------------------+-----------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_rps_zones` |
+-------------------------------+-----------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_rps_zones`       |
+-------------------------------+-----------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+---------------------------------------+
|:code:`scenarios` table column |:code:`project_rps_zone_scenario_id`   |
+-------------------------------+---------------------------------------+
|:code:`scenario` table feature |:code:`of_rps`                         |
+-------------------------------+---------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_rps_zones` |
+-------------------------------+---------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_rps_zones`       |
+-------------------------------+---------------------------------------+

Target
======

Relevant tables:

+-------------------------------+--------------------------------+
|:code:`scenarios` table column |:code:`rps_scenario_id`         |
+-------------------------------+--------------------------------+
|:code:`scenario` table feature |:code:`of_rps`                  |
+-------------------------------+--------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_rps` |
+-------------------------------+--------------------------------+
|:code:`input_` tables          |:code:`inputs_system_rps`       |
+-------------------------------+--------------------------------+

==========
Carbon Cap
==========

Relevant tables:

+-------------------------------+------------------------------------------------+
|:code:`scenarios` table column |:code:`carbon_cap_zone_scenario_id`             |
+-------------------------------+------------------------------------------------+
|:code:`scenario` table feature |:code:`of_carbon_cap`                           |
+-------------------------------+------------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_geography_carbon_cap_zones` |
+-------------------------------+------------------------------------------------+
|:code:`input_` tables          |:code:`inputs_geography_carbon_cap_zones`       |
+-------------------------------+------------------------------------------------+

Contributing Projects
=====================

Relevant tables:

+-------------------------------+----------------------------------------------+
|:code:`scenarios` table column |:code:`project_carbon_cap_zone_scenario_id`   |
+-------------------------------+----------------------------------------------+
|:code:`scenario` table feature |:code:`of_carbon_cap`                         |
+-------------------------------+----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_carbon_cap_zones` |
+-------------------------------+----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_carbon_cap_zones`       |
+-------------------------------+----------------------------------------------+

Target
======

Relevant tables:

+-------------------------------+---------------------------------------+
|:code:`scenarios` table column |:code:`carbon_cap_scenario_id`         |
+-------------------------------+---------------------------------------+
|:code:`scenario` table feature |:code:`of_carbon_cap`                  |
+-------------------------------+---------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_system_carbon_cap` |
+-------------------------------+---------------------------------------+
|:code:`input_` tables          |:code:`inputs_system_carbon_cap`       |
+-------------------------------+---------------------------------------+


.. _database-testing-section-ref:

*************************
Database Input Validation
*************************

Once you have built the database with a set of scenarios and associated inputs,
you can test the inputs for a given scenario by running the inputs validation
suite. This suite will extract the inputs for the scenario of interest and
check whether the inputs are valid. A few examples of invalid inputs are:
 - required inputs are missing
 - inputs are the wrong datatype or not in the expected range
 - inputs are inconsistent with a related set of inputs
 - inputs are provided but not used

After the validation is finished, any encountered input validations are dumped
into the :code:`status_validation` table. This table contains the following
columns:

 - :code:`scenario_id`: the scenario ID of the scenario that is validated.
 - :code:`subproblem_id`: the subproblem ID of the subproblem that is
   validated (the validation suite validates each subproblem separately).
 - :code:`stage_id`: the stage ID of the stage that is validated (the
   validation suite validates each stage separately).
 - :code:`gridpath_module`: the GridPath module that returned the validation
   error.
 - :code:`related_subscenario`: the subscenario that is related to the
   validation error.
 - :code:`related_database_table`: the database table that likely contains
   the validation error.
 - :code:`issue_severity`: the severity of the validation error. "High"
   means the model won't be able to run. "Mid" means the model might run, but
   the results will likely be unexpected. "Low" means the model should run and
   the results are likely as expected, but there are some inconsistencies
   between the inputs.
 - :code:`issue_type`: a short description of the type of validation error.
 - :code:`issue_description`: a detailed description of the validation error.
 - :code:`timestamp`: lists the exact time when the validation error
   encountered.

Note that the input validation suite is not exhaustive and does not catch
every possible input error. As we continue to develop and use GridPath, we
expect that the set of validation tests will expand and cover more and more
of the common input errors.

To run the validation suite from the command line, navigate to the
:code:`gridpath/gridpath` folder and type::

    validate_inputs.py --scenario SCENARIO_NAME --database PATH/TO/DATABASE
