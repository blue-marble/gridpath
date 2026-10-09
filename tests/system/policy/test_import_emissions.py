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
The import-emissions helpers shared by the carbon cap and carbon tax (and by
any policy with a composite zone key or horizon-level enforcement): index
splitting and the validation helpers, with one- and two-column zone keys.
"""

import unittest

import pandas as pd

from gridpath.system.policy.import_emissions import (
    CARBON_CAP,
    GROSS,
    NET_PRD,
    ImportEmissionsPolicy,
    ImportEmissionsSource,
    period_keys,
    split_index,
    validate_export_intensities,
    validate_zones,
    zone_scope_sql,
)
from gridpath.system.markets.carbon_emissions_common import MARKET_SOURCE
from gridpath.transmission.operations.carbon_emissions_common import TX_SOURCE


class _Mod(object):
    """A stand-in model with a period per timepoint."""

    period = {1: 2020, 2: 2020, 3: 2030}


class _Subscenarios(object):
    CARBON_CAP_ZONE_SCENARIO_ID = 7
    POLICY_ZONE_SCENARIO_ID = 3


# A policy enforced over (policy_name, policy_zone, balancing_type, horizon)
COMPOSITE = ImportEmissionsPolicy(
    name="policy",
    zone_columns=["policy_name", "policy_zone"],
    zones_set="POLICIES_ZONES",
    requirement_set="POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ",
    requirement_columns=["balancing_type_horizon", "horizon"],
    requirement_keys=lambda mod, tmp: [("year", mod.period[tmp])],
    zone_subscenario_attr="POLICY_ZONE_SCENARIO_ID",
    results_df="policy_zone_period_df",
    import_emission_components="x",
    signed_import_emission_components="y",
)


class TestImportEmissionsHelpers(unittest.TestCase):
    def test_policy_descriptor(self):
        self.assertEqual(1, CARBON_CAP.zone_dimen)
        self.assertEqual(["carbon_cap_zone", "period"], CARBON_CAP.index_columns)
        self.assertEqual(("Zone1",), CARBON_CAP.zone_of(("Zone1", 2020)))
        self.assertEqual([(2020,)], period_keys(_Mod(), 1))

        self.assertEqual(2, COMPOSITE.zone_dimen)
        self.assertEqual(
            ["policy_name", "policy_zone", "balancing_type_horizon", "horizon"],
            COMPOSITE.index_columns,
        )
        self.assertEqual(
            ("CarbonCap", "Zone1"),
            COMPOSITE.zone_of(("CarbonCap", "Zone1", "year", 2020)),
        )

    def test_split_index(self):
        # Transmission line, one-column zone
        self.assertEqual(
            (("Tx1",), ("Zone1",), 20200101),
            split_index(TX_SOURCE, ("Tx1", "Zone1", 20200101)),
        )
        # Transmission line, two-column zone
        self.assertEqual(
            (("Tx1",), ("CarbonCap", "Zone1"), 20200101),
            split_index(TX_SOURCE, ("Tx1", "CarbonCap", "Zone1", 20200101)),
        )
        # (load zone, market) pair, one- and two-column zones
        self.assertEqual(
            (("LZ1", "Market1"), ("Zone1",), 20200101),
            split_index(MARKET_SOURCE, ("LZ1", "Market1", "Zone1", 20200101)),
        )
        self.assertEqual(
            (("LZ1", "Market1"), ("CarbonCap", "Zone1"), 20200101),
            split_index(
                MARKET_SOURCE, ("LZ1", "Market1", "CarbonCap", "Zone1", 20200101)
            ),
        )

    def test_zone_scope_sql(self):
        sql = zone_scope_sql(_Subscenarios(), CARBON_CAP)
        self.assertIn("(carbon_cap_zone) IN (", sql)
        self.assertIn("inputs_geography_carbon_cap_zones", sql)
        self.assertIn("carbon_cap_zone_scenario_id =\n                7", sql)

        sql = zone_scope_sql(_Subscenarios(), COMPOSITE)
        self.assertIn("(policy_name, policy_zone) IN (", sql)
        self.assertIn("SELECT policy_name, policy_zone", sql)
        self.assertIn("inputs_geography_policy_zones", sql)

    def test_validate_zones(self):
        df = pd.DataFrame(
            {
                "transmission_line": ["Tx1", "Tx2"],
                "policy_name": ["CarbonCap", "CarbonCap"],
                "policy_zone": ["Zone1", "Zone9"],
            }
        )
        basis_by_zone = {("CarbonCap", "Zone1"): GROSS}
        errors = validate_zones(df, basis_by_zone, ["transmission_line"], COMPOSITE)
        self.assertEqual(1, len(errors))
        self.assertIn("Tx2-CarbonCap-Zone9", errors[0])
        self.assertNotIn("Tx1-CarbonCap-Zone1", errors[0])

        basis_by_zone[("CarbonCap", "Zone9")] = NET_PRD
        self.assertEqual(
            [], validate_zones(df, basis_by_zone, ["transmission_line"], COMPOSITE)
        )

    def test_validate_export_intensities(self):
        df = pd.DataFrame(
            {
                "transmission_line": ["Tx1", "Tx2", "Tx3"],
                "policy_name": ["CarbonCap"] * 3,
                "policy_zone": ["Zone1", "Zone1", "Zone2"],
                "import_intensity": [0.5, 0.5, 0.5],
                "export_intensity": [0.6, 0.4, 0.6],
                "tmp_import_emissions_scenario_id": [None, None, None],
            }
        )
        basis_by_zone = {("CarbonCap", "Zone1"): NET_PRD, ("CarbonCap", "Zone2"): GROSS}
        errors = validate_export_intensities(
            df, basis_by_zone, pd.DataFrame(), ["transmission_line"], COMPOSITE
        )
        # Only the net zone's offending row is reported
        self.assertEqual(1, len(errors))
        self.assertIn("Tx1-CarbonCap-Zone1", errors[0])


if __name__ == "__main__":
    unittest.main()
