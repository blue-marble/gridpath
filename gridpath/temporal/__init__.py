#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
gridpath.temporal
^^^^^^^^^^^^^^^^^

The **gridpath.temporal** package describes the optimization problem's temporal
span and resolution.

Temporal units include:

*Timepoints*: the finest resolution over which operational decisions are
made (e.g. an hour). Commitment and dispatch decisions are made for each
timepoint, with some constraints applied across timepoint (e.g. ramp
constraints.)

*Horizons*: Each timepoint belongs to a 'horizon' (e.g. a day),
which describes which timepoints are linked together, with some operational
constraints enforced over the 'horizon,' e.g. hydro budgets or storage
energy balance.

*Periods*: each timepoint and horizon belong to a 'period' (e.g. an year),
which describes when decisions to build or retire infrastructure can be made.

.. TODO:: we need some examples of various types of temporal setups we could
    have, e.g. 8760 hours, day by day (horizon weights are 1), 1 period; 8760
    hours, week by week (horizon weights are 1), 12 periods (discount factors
    could be kept at 1, but number_years_represented would be the number of
    days per month divided by 365).
"""
