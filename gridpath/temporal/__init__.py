#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describes the optimization problem's temporal resolution. Temporal units
include:

*Timepoints*: the finest resolution over which operational decisions are
made (e.g. an hour).

*Horizons*: Each timepoint belongs to a 'horizon' (e.g. a day),
which describes which timepoints are linked together, with some operational
constraints enforced over the 'horizon,' e.g. hydro budgets or storage
energy balance.

*Periods*: each timepoint and horizon belong to a 'period' (e.g. an year),
which describes when decisions to buid or retire infrastructure can be made.
"""
