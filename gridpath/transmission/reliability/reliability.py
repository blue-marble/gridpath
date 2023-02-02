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
Transmission lines linking PRM zones. Note that the capacity transfer variable is not
at the transmission line level -- it is defined at the "capacity transfer link"
level, with the transmission line topology used to limit total transfers on each link.
"""

import csv
import os.path
from pyomo.environ import Set, Param


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`PRM_TX_LINES`                                                  |
    |                                                                         |
    | The set of PRM-relevant transmission lines.                             |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`prm_zone_from`                                                 |
    | | *Defined over*: :code:`PRM_TX_LINES`                                  |
    | | *Within*: :code:`PRM_ZONES`                                           |
    |                                                                         |
    | The transmission line's starting PRM zone.                              |
    +-------------------------------------------------------------------------+
    | | :code:`prm_zone_to`                                                  |
    | | *Defined over*: :code:`TX_LINES`                                      |
    | | *Within*: :code:`PRM_ZONES`                                           |
    |                                                                         |
    | The transmission line's ending PRM zone.                                |
    +-------------------------------------------------------------------------+


    """
