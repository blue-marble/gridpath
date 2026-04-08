# Copyright 2026 Sylvan Energy Analytics LLC.
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
Flat-block SOD compliance type.

Contributes the project's full capacity (MW) in every (period, month, hour)
covered by a month-hour policy requirement. Completely decoupled from
operational timepoints — no connection to dispatch or energy accounting.
"""


def contribution_in_month_hour(mod, prj, policy, zone, prd, mn, hr):
    """
    Full capacity counts in every SOD hour, regardless of dispatch.
    Only valid for month-hour policy requirements.
    """
    if (prj, prd) in mod.PRJ_OPR_PRDS:
        return mod.Capacity_MW[prj, prd]
    else:
        return 0
