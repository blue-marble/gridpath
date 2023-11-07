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
