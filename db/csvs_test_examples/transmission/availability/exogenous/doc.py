# Copyright 2016-2020 Blue Marble Analytics LLC.
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

**Relevant tables:**

+---------------------------+---------------------------------------------------------+
|:code:`subscenario_` table |:code:`subscenarios_transmission_availability_exogenous` |
+---------------------------+---------------------------------------------------------+
|:code:`input_` table       |:code:`inputs_transmission_availability_exogenous`       |
+---------------------------+---------------------------------------------------------+

Within each :code:`transmission_availability_scenario_id`, a transmission  line
of the :code:`exogenous` *availability type* can point to a particular
:code:`exogenous_availability_scenario_id`, the data for which is contained
in the :code:`inputs_transmission_availability_exogenous` table. The names and
descriptions of each :code:`transmission` and
:code:`exogenous_availability_scenario_id` combination are in the
:code:`subscenarios_transmission_availability_exogenous` table. The
availability derate for each combination is defined by stage and timepoint,
and must be greater than or equal to 0 (0=full derate). Values more than 1
are allowed.

"""

if __name__ == "__main__":
    print(__doc__)
