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

+-------------------------------+-----------------------------------------------+
|:code:`scenarios` table column |:code:`project_regulation_up_ba_scenario_id`   |
+-------------------------------+-----------------------------------------------+
|:code:`scenario` table feature |:code:`of_regulation_up`                       |
+-------------------------------+-----------------------------------------------+
|:code:`subscenario_` table     |:code:`subscenarios_project_regulation_up_bas` |
+-------------------------------+-----------------------------------------------+
|:code:`input_` tables          |:code:`inputs_project_regulation_up_bas`       |
+-------------------------------+-----------------------------------------------+


One row per project and balancing area. A project may be mapped to several
balancing areas: it then splits its total provision among them in each
timepoint, and :code:`max_fraction_of_provision` caps the share of the total
that may go to each balancing area (blank = 1, i.e. no cap; the caps of a
project's balancing areas must sum to at least 1). Rows for balancing areas
not in the scenario's :code:`regulation_up_ba_scenario_id` are ignored.
"""

if __name__ == "__main__":
    print(__doc__)
