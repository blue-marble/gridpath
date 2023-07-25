# Copyright 2016-2022 Blue Marble Analytics LLC.
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

import os.path
from pyomo.environ import value


# Import-export rules


# Export & import if USE is found only
def export_rule_use(instance, quiet):
    unserved_energy_found = any(
        [
            value(instance.Unserved_Energy_MW_Expression[z, tmp])
            for z in getattr(instance, "LOAD_ZONES")
            for tmp in getattr(instance, "TMPS")
        ]
    )

    if unserved_energy_found:
        if not quiet:
            print("unserved energy found; exporting results")

    return unserved_energy_found


def summarize_results_use(scenario_directory, subproblem, stage, quiet):
    if os.path.exists(
        os.path.join(
            scenario_directory,
            subproblem,
            stage,
            "results",
            "system_load_zone_timepoint.csv",
        )
    ):
        return True
    else:
        if not quiet:
            print("skipping results summary")
        return False


def import_rule_use(results_directory, quiet):
    if os.path.exists(
        os.path.join(results_directory, "system_load_zone_timepoint.csv")
    ):
        import_results = True
        if not quiet:
            print("unserved energy found -- importing")
    else:
        import_results = False
        if not quiet:
            print("no unserved energy -- skipping")

    return import_results


import_export_rules = {
    "USE": {
        "export": export_rule_use,
        "summarize": summarize_results_use,
        "import": import_rule_use,
    }
}
