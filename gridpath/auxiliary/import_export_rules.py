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
def export_rule_use(instance):
    unserved_energy_found = any(
        [
            value(instance.Unserved_Energy_MW_Expression[z, tmp])
            for z in getattr(instance, "LOAD_ZONES")
            for tmp in getattr(instance, "TMPS")
        ]
    )

    if unserved_energy_found:
        print("unserved energy found; exporting results")

    return unserved_energy_found


def summarize_results_use(scenario_directory, subproblem_directory, stage_directory):
    if os.path.exists(
        os.path.join(
            scenario_directory,
            subproblem_directory,
            stage_directory,
            "results",
            "load_balance.csv",
        )
    ):
        return True
    else:
        print("skipping results summary")
        return False


def import_rule_use(results_directory):
    if os.path.exists(os.path.join(results_directory, "load_balance.csv")):
        import_results = True
        print("unserved energy found -- importing")
    else:
        import_results = False
        print("no unserved energy -- skipping")

    print("Import results is ", import_results)
    return import_results


import_export_rules = {
    "USE": {
        "export": export_rule_use,
        "summarize": summarize_results_use,
        "import": import_rule_use,
    }
}
