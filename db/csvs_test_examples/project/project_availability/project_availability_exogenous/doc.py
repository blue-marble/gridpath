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

"""

if __name__ == "__main__":
    print(__doc__)
