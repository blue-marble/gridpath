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

+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table column  |:code:`transmission_availability_scenario_id`  |
+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table feature |N/A                                            |
+--------------------------------+-----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_transmission_availability` |
+--------------------------------+-----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_transmission_availability`       |
+--------------------------------+-----------------------------------------------+

All transmission lins in a GridPath scenario must be a assigned an
*availability type*, which determines whether their capacity is operational
in each timepoint in which the capacity exists. All implemented availability types are
listed in the :code:`mod_tx_availability_types` table.

Each line's availability type are given in the
:code:`inputs_transmission_availability`. The availability types currently
implemented include :code:`exogenous` (availability is determined outside of
a GridPath model via the data fed into it) and two endogenous types:
:code:`binary` and :code:`continuous` that require certain inputs that
determine how availability is constrained in the GridPath model. See the
:ref:`transmission-availability-type-section-ref` section for more info. In
addition to the transmission availability types, the
:code:`inputs_transmission_availability` table contains the information for
how to find any additional data needed to determine transmission availability with
the :code:`exogenous_availability_scenario_id` and
:code:`endogenous_availability_scenario` columns for the endogenous and
exogenous types respectively. The IDs in the former column are linked to the
data in the :code:`inputs_transmission_availability_exogenous` table and in the
latter column to the :code:`inputs_transmission_availability_endogenous` table.
For transmissions of the :code:`exogenous` availability type, if the value is in the
:code:`exogenous_availability_scenario_id` column is NULL, no availability
capacity derate is applied by GridPath. For transmissions of a :code:`binary` of
:code:`continuous` availability type, a value in the
:code:`endogenous_availability_scenario_id` is required.

"""

if __name__ == "__main__":
    print(__doc__)
