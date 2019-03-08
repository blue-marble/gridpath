*******************
Basic Functionality
*******************

GridPath can be used to create optimization problems with different features
and varying levels of complexity. For the basic model, the user must
define the model's temporal setup (e.g. 365 individual days at an hourly
resolution), the geographic setup (e.g. a single load zone), the
availability and operating characteristics of the generation infrastructure
(e.g. an existing 500-MW coal plant with a specified heat rate), and the
desired objective (e.g. minimize cost).

Temporal Setup
==============

GridPath's temporal span and resolution is flexible: the user can decide on
a temporal setup by assigning appropriate weights to and relationships among
GridPath's temporal units.

The temporal units include:

**Timepoints**

Timepoints are the finest resolution over which operational decisions are
made (e.g. an hour). Generator commitment and dispatch decisions are made for
each timepoint, with some constraints applied across timepoint (e.g. ramp
constraints.) Most commonly, a timepoint is an hour, but the resolution is
flexible: a timepoint could also be a 15-minute, 5-minute, 1-minute, or 4-hour
segment. Different timepoint durations can also be mixed, so some can be
5-minute segments and some can be hours.

**Horizons**

Each timepoint belongs to a 'horizon' that describes how
timepoints are grouped together when making operational decisions, with some
operational constraints enforced over the 'horizon,' e.g. hydro budgets or
storage energy balance. Horizons are modeled as independent from each other
for operational purposes (i.e operational decisions made on one horizon do
not affect those made on another horizon). A 'horizon' is most commonly a
day -- e.g. we usually model a year of system operations a day at a time --
but can be any other duration, e.g. we could model the year a week at a
time, a month at a time, etc. Horizon durations can also be mixed. The
horizon boundary condition can be 'circular' or 'linear.' With the
'circular' approach, the last timepoint of the horizon is considered the
previous timepoint for the first timepoint of the horizon (for the purposes
of functionality such as ramp constraints or tracking storage state of
charge). If the boundary is 'linear,' then we ignore constraints relating to
the previous timepoint in the first timepoint of a horizon.

In production simulation, we usually optimize a single horizon at a time (e.g.
each of the year's 365 days is modeled individually) and sum the results. In
a capacity-expansion model, we usually include multiple horizons in the same
optimization (but they are independent from each other for operational
purposes). In a capacity-expansion context, however, we usually do not model
the full study period explicitly; instead, due to computational
constraints, we use a sample of horizons and assign weights to them in order
to represent the full set of horizons (e.g. use one day per month to
represent the whole month using the number of day in that
month for the horizon weight).

GridPath also has multi-stage commitment functionality, i.e. decisions made
for a horizon can be fixed and the feed into a next stage with some updated
parameters (e.g. an updated load and renewable output forecast). The number
of stages is flexible and the timepoint resolution can change from stage to
stage.

.. todo: don't remember if we can change the timepoint resolution from stage
    to stage yet?

**Periods**

Each timepoint and horizon belong to a 'period' (e.g. an year),
which describes when decisions to build or retire infrastructure can be made.
In a production-cost simulation context, we can use the period to
exogenously change the amount of available capacity, but the 'period'
temporal unit is mostly used i n the capacity-expansion approach, as it
defines when capacity decisions are made and new infrastructure becomes
available (or is retired). That information in turn feeds into the horizon-
and timepoint-level operational constraints, i.e. once a generator is build,
the optimization is allowed to operate in subsequent periods (usually for the
duration of the generators's lifetime). The 'period' resolution is also
flexible: e.g. capacity decisions can be made every month, every year, every
10 years, etc.


Geographic Setup
================

The main geographic unit in GridPath is the **load zone**. The load zone is
the level at which the load-balance constraints are enforced. In GridPath,
we can model a single load zone (copper plate) or multiple load zones, which
can be connected with transmission. This flexibility makes it possible to
apply to different regions with different geographic set-up or to take
different geographic approaches in modeling the same region (e.g. higher or
lower zonal resolution for the same region).

Optional levels of geographic resolution include **balancing areas** for
reserve requirements and **policy zones**. In GridPath, it is possible
for generators in the same load zone to contribute to different reserve
balancing areas and/or policy zones.

Projects
========

Generation, storage, and load-side resources in GridPath are called
**projects**. Each project is associated with a *load zone* whose load-balance
constraint it constraint it contributes to. In addition, each project is
assigned a *capacity type* and an *operational type*. These types are
described in more detail below.

Project Capacity
----------------
Each project in GridPath must be assigned a *capacity type*. The *capacity
type* determines the available capacity and the capacity-associated costs of
generation, storage, and demand-side infrastructure 'projects' in the
optimization problem. The currently implemented capacity types include:

Specified Generation
^^^^^^^^^^^^^^^^^^^^

This capacity type describes generators that are available to the optimization
without having to incur an investment cost, e.g. existing generators or
generators that will be built in the future and whose capital costs we want
to ignore (in the objective function). A specified generator can be available
in all periods, or in some periods only, with no restriction on the order
and combination of periods. The user may specify a fixed O&M cost for these
generators, but this cost will be a fixed number in the objective function
and will therefore not affect any of the optmization decisions.


Specified Generation with Linear Economic Retirement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This capacity type describes generators with the same characteristics as
*specified generation*, but whose fixed O&M cost can be avoided by
'retiring' them. The optimization can make the decision to retire generation
in each study period. Once retired, the generator may not become operational
again. Retirement decisions for this capacity type are 'linearized,' i.e.
the optimization may retire generators partially (e.g. retire only 200 MW of
a 500-MW generator).

Linear New-Build Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^^
This capacity type describes generation that can be built by the
optimization at a cost. These investment decisions are linearized, i.e.
the decision is not whether to build a unit of a specific size (e.g. a
50-MW combustion turbine), but how much capacity to build at a particular
project. Once built, the capacity remains available for the duration of the
project's pre-specified lifetime. Minimum and maximum capacity constraints
can be optionally implemented.

Specified Storage
^^^^^^^^^^^^^^^^^

This capacity type describes the power (i.e. charging and discharging
capacity) and energy capacity (i.e. duration) of storage projects that are
available to the optimization without having to incur an investment cost.
For example, it can be applied to existing storage projects or to
storage projects that will be built in the future and whose capital costs we
want to ignore (in the objective function).

It is not required to specify a capacity for all periods, i.e. a project can
be operational in some periods but not in others with no restriction on the
order and combination of periods.

Linear New-Build Storage
^^^^^^^^^^^^^^^^^^^^^^^^
This capacity type describes storage projects that can be built by the
optimization at a cost. Investment decisions made separately for the
project's power capacity and its energy capacity, therefore endogenously
determine the sizing of the storage. The decisions are linearized (i.e. the
model decides how much power capacity and how much energy capacity to build
at a project, not whether or not to built a project of pre-defined capacity).
Once built, these storage projects remain available for the duration of their
pre-specified lifetime. Minimum and maximum power capacity and duration
constraints can be optionally implemented.

Shiftable Load Supply Curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^
This capacity type describes a supply curve for new shiftable load capacity.
This type is a custom implementation for GridPath projects in the California
Integrated Resource Planning proceeding.

Capacity types to be implemented include:

Binary New-Build Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^^
This capacity type describes pre-specified generators (i.e. generators with
a pre-specified capacity) that can be built by the optimization at a cost.
These investment decisions are binary, i.e. the optimization decides whether
or not to build the project. Once built, the capacity remains available for
the duration of the project's pre-specified lifetime.


Binary New-Build Storage
^^^^^^^^^^^^^^^^^^^^^^^^
This capacity type describes pre-specified storage projects that can be built
by the optimization at a cost. The decisions are binary (i.e. the
model decides how whether or not to built a project of pre-defined power and
energy capacity). Once built, these storage projects remain available for
the duration of their pre-specified lifetime.

Specified Generation with Binary Economic Retirement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This capacity type describes generators with the same characteristics as
*specified generation*, but whose fixed O&M cost can be avoided by
'retiring' them. The optimization can make the decision to retire generation
in each study period. Once retired, the generator may not become operational
again. Retirement decisions for this capacity type are binary, i.e.
'partial' retirements are not allowed.

Other
^^^^^
TBD


Project Operations
------------------
Each project in GridPath must be assigned a *operational type*. The
*operational_type* determines the operational capabilities of a project. The
currently implemented operational types include:

Must-Run
^^^^^^^^
This operational type describes generators that produce constant power equal
to their capacity in all timepoints when they are available. They cannot
provide reserves. Costs for this operational type include fuel costs and
variable O&M costs.

Dispatchable Always-On
^^^^^^^^^^^^^^^^^^^^^^
This operational type describes generators that must produce power in all
timepoints they are available; unlike the must-run generators, however, they
can vary power output between a pre-specified minimum stable level (greater
than 0) and their available capacity. Always-on generators cannot provide
reserves. Ramp rate limits can be optionally specified. Costs for this
operational type include fuel costs and variable O&M costs.

Dispatchable Binary-Commit
^^^^^^^^^^^^^^^^^^^^^^^^^^
This operational types describes generators that can be turned on and off,
i.e. that have binary commitment variables associated with them. If they are
committed, these generators can vary power output between a pre-specified
minimum stable level (greater than 0) and their available capacity. Heat
rate degradation below full load is considered. If the generators are not
committed, power output is 0. The optimization makes commitment and power
output decisions in every timepoint. These generators can optionally be
allowed to provide upward and/or downward reserves. Additional functionality
will include ramp rate limits as well us minimum up and down time
constraints. Starts and stops -- and the associated cost and emissions --
can be tracked and constrained for these generators. Costs for this
operational type include fuel costs, variable O&M costs, and startup and
shutdown costs.


Dispatchable Continuos-Commit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This operational type is the same as the 'dispatchable binary commit' type,
but the commitment decision are declared as continuous (with bounds of 0 to
1) instead of binary, so 'partial' generators can be committed. This
treatment can be helpful in situations when mixed-integer problem runtimes
are long and is similar to loosening the MIP gap (but can target specific
generators). The 'continuous-commit' generators can vary power output
between a minimum loading level (specified as a fraction of committed
capacity) and the committed capacity in every timepoint. Costs for this
operational type include fuel costs, variable O&M costs, and startup and
shutdown costs.

Dispatchable No-Commit
^^^^^^^^^^^^^^^^^^^^^^
This operational type describes generators that can vary their output
between 0 and full capacity in every timepoint in which they are available
(i.e. they have power output variable but no commitment variables associated
with them). The heat rate of these generators does not degrade below full
load and they can be allowed to provide upward and/or downward reserves.
Costs for this operational type include fuel costs, variable O&M costs, and
startup and shutdown costs.

Dispatchable Capacity-Commit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This operational type is similar to the 'dispatchable continuous commit'
operational type but is particularly well suited for application to 'fleets'
of generators with the same characteristics. For example, we could have a
GridPath project with a total capacity of 2000 MW, which actually consists
of four 500-MW units. The optimization decides how much total capacity to
commit (i.e. turn on), e.g. if 2000 MW are committed, then four generators (x
500 MW) are on and if 500 MW are committed, then one generator is on, etc.
The capacity commitment decision variables are continuous. This approach
makes it possible to reduce problem size by grouping similar generators
together and linearizing the commitment decisions.

The optimization makes the capacity-commitment and dispatch decisions in
every timepoint. Project power output can vary between a minimum loading level
(specified as a fraction of committed capacity) and the committed capacity
in each timepoint when the project is available. Heat rate degradation below
full load is considered. These projects can be allowed to provide upward
and/or downward reserves.

No standard approach exists for applying ramp rate and minimum up and down
time constraints to this operational type. GridPath does include
experimental functionality for doing so. Starts and stops -- and the
associated cost and emissions -- can also be tracked and constrained for
this operational type.

Costs for this operational type include fuel costs, variable O&M costs, and
startup and shutdown costs.


Hydro Curtailable
^^^^^^^^^^^^^^^^^
This operational type describes the operations of hydro generation. These
projects can vary power output between a minimum and maximum level specified
for each horizon, and must produce a pre-specified amount of energy on each
horizon when they are available, some of which may be curtailed. The
curtailable hydro projects can be allowed to provide upward and/or downward
reserves. Timepoint-to-timepoint ramp rate limits can optionally be enforced.
Costs for this operational type include variable O&M costs.

Hydro Non-Curtailable
^^^^^^^^^^^^^^^^^^^^^
This operational type describes the operations of hydro generation and is
like the 'hydro curtailable' operational type except that curtailment is not
allowed.

Variable
^^^^^^^^
This operational type describes generators whose power output is equal to a
pre-specified fraction of their available capacity (a capacity factor
parameter) in every timepoint. Curtailment is allowed. GridPath includes
experimental features to allow these generators to provide upward and/or
downward reserves. Costs for this operational type include variable O&M costs.

Variable Non-Curtailable
^^^^^^^^^^^^^^^^^^^^^^^^
This operational type is like the 'variable' type except that curtailment is
not allowed.

Storage Generic
^^^^^^^^^^^^^^^
This operational type describes a generic storage resource. It can be
applied to a battery or to a pumped hydro project or another storage
technology. The type is associated with three main variables in each
timepont when the project is available: the charging level, the discharging
level, and the energy available in storage. The first two are constrained to
be less than or equal to the project's power capacity. The third is
constrained to be less than or equal to the project's energy capacity. The
model tracks the stage of charge in each timepoint based on the charging and
discharging decisions in the previous timepoint, with adjustments for
charging and discharging efficiencies. Storage projects can be allowed to
provide upward and/or downward reserves. Costs for this operational type
include variable O&M costs.

Shiftable Load Generic
^^^^^^^^^^^^^^^^^^^^^^
This operational type describes a generic shiftable load resource. There are
two opertional variables in each timepoint: one for shifting load up (adding
load) and another for shifting load down (subtracting load). These cannot
exceed the power capacity of the project and must meet an energy balance
constrain on each horizon. Efficiency losses are not currently implemented.
There are two opertional variables: shift load up (add load) and shift load
down (subtract load). These cannot exceed the power capacity of the project
and must meet an energy balance constraint on each horizon (no efficiency
loss implemented).


Load Balance
============

Objective Function
==================

**********************
Advanced Functionality
**********************

Transmission
============

Operating Reserves
==================

Reliability
===========

Policy
======

Custom Modules
==============


**********
Approaches
**********

GridPath can be used in production-cost simulation or capacity-expansion mode
depending on whether "projects" of the "new_build" capacity types are included
in the model. To be implemented is functionality to change the objective
function in order to be able to take an asset-valuation approach (i.e. profit-
maximization instead of cost-minimization) or optimize for something other
than cost (e.g. minimize CO2 emissions).

Production-Cost Simulation
==========================

Capacity-Expansion
==================

While production cost simulation models seek to optimize the operations of a
power system with a fixed set of resources specified by the user,
capacity-expansion models are designed to understand how the system should
evolve over time: they try to answer the question of what resources to
invest in among many options in order to meet system goals over time, i.e.
what grid infrastructure is most cost-effective while ensuring that the
system operates reliably while meeting policy targets.

The capacity expansion model minimizes the overall system cost over some
planning horizon, considering both capital costs (generators, transmission,
storage, any asset) and variable or operating costs subject to various
technical (e.g. generator limits, wind and solar availability, transmission
limits across corridors, hydro limits) and policy constraints (e.g.
renewable energy mandates, GHG targets).

Because capacity expansion models have to optimize over several years or
decades, selecting generation, and transmission assets from many different
available options, the problem can get large quickly. In order to have
reasonable runtime, these models often simplify aspects of the electricity
grid, both in space and time. Spatially, most models will consider only
balancing areas or states as nodes (so all substations with the BA are
clubbed together). Temporally, only representative days and hours may be
used, and then given weights to represent a whole year e.g. one day per
month, and either 24 hours, or 6 time blocks (each representing 4 hours).
This simplification makes the linear optimization problem tractable. If the
spatial resolution is small, the temporal resolution may be increased, and
vice versa.

After the system is “built”, the system should be simulated for the entire
year (or years) using a production cost model to ensure that the decisions
we made using representative time slices can operate reliably at every time
point of the year. The production cost model takes a given electric system
(similar to the Greening-the-Grid study that used the CEA plans) and solves
the model to ensure demand equals supply, and all constraints like generator
limits, transmission flows, ramp rates, and policy constraints are all met.

Capacity-expansion and production cost models are therefore complementary.
The former allows us to quickly explore many options for how the power
system ought to evolve over time and find the optimal solution; the latter
can help us ensure that the system we design does in fact perform as we
intended (e.g. that it serves load reliably and meets policy targets).



Other
=====

Linear, Mixed-Integer, and Non-Linear Formulations
==================================================

Depending on how modules are combined, linear, mixed-integer, and non-linear
problem formulations are possible in GridPath.
