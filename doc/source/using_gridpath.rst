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

Geographic Setup
================

Projects
========

Project Capacity
----------------

Project Operations
------------------

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
