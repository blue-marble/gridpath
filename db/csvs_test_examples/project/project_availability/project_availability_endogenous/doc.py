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


"""

if __name__ == "__main__":
    print(__doc__)
