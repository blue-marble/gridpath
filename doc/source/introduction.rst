*****************
Intro to GridPath
*****************

Motivation
==========

Transitioning to a low-carbon electricity system poses numerous new
challenges to system planners and operators. Variable renewable energy
technologies such as wind and solar introduce variability and uncertainty to
system operations, requiring thoughtful integration and the deployment of
balancing technologies such as energy storage and load response. Technology
characteristics and costs are evolving rapidly, introducing risk for project
developers and investors as well as for policymakers and planners concerned
about the economic impact on consumers. In that context, good planning
becomes increasingly important and advanced software tools can help to
rapidly and continuously evaluate and plan the electricity system.

Traditional power-system models are often not designed to address the many new
questions arising from the shift to renewable and low-carbon resources,
storage, widespread electric vehicle and building electrification, and load
participation in system operations. This was the main motivation for
GridPath's development. Furthermore, our goal is to create a transparent and
user-friendly platform that facilitates quick model development and rapid
adaptation.

What is GridPath?
=================

GridPath is a comprehensive grid analytics platform that integrates several
types of power system modeling approaches, including multi-stage
production-cost simulation, long-term capacity expansion, and
(eventually) price-based asset valuation.

GridPath has a modular architecture that makes it possible to combine
modules to create optimization problems with varying features and levels of
complexity. Linear, mixed-integer, and non-linear formulations are possible
depending on the selected modules.

The main variables fall into two categories:

#. Capacity: whether (generator, storage, and/or transmission) capacity should be built or retired?
#. Operations: how should available (generator, storage, and/or transmission) capacity be operated?

The main constraints include:

#. Capacity: limits on the amount of capacity that can be deployed.
#. Operations: limits on the operational capabilities of generation, storage, and transmission assets.
#. System: meeting load, operating reserves, and reliability requirements.
#. Policy: meeting policy targets.

The objective function is typically to minimize system costs, but other
formulations are possible.

GridPath can simulate the operations of the power system, capturing the
capabilities of and constraints on generation, storage, and transmission
resources to understand grid integration and flexibility needs. In
capacity-expansion mode, GridPath can also identify cost-effective
deployment of conventional and renewable generation as well as storage,
transmission lines, and demand response.

GridPath has a flexible temporal and spatial resolution, and is designed for
easy application to different regions and systems. Each generation, storage,
and transmission resource can be modeled with a user-specified level of
detail. The platform can also optionally capture the effects on operations
and the optimal resource portfolio of forecast error, provision of ancillary
grid services, interconnection, reliability requirements such as a planning
reserve margin, and policies such as a renewables portfolio standard (RPS) or
a carbon cap.

Each generation, storage, and transmission asset can be modeled
with a user-specified level of detail. Combined with a flexible temporal and
spatial resolution, GridPath’s modularity facilitates its application to
different systems and regions. The decision for what to simplify and what
requires a detailed treatment is left up to the user depending on the
application of interest.

GridPath is under active development and we are continuously adding new
functionality.
