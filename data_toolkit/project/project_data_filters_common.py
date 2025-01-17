# Copyright 2016-2024 Blue Marble Analytics LLC.
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


# TODO: make it easier to include or exclude proposed
def get_eia860_sql_filter_string(study_year, region):
    eia860_sql_filter_string = f"""
    (unixepoch(current_planned_generator_operating_date) < unixepoch(
     '{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
     AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
     AND balancing_authority_code_eia in (
         SELECT baa
         FROM user_defined_baa_key
         WHERE region = '{region}'
     )
     AND operational_status_code in ('OP', 'CO')
    """

    return eia860_sql_filter_string


FUEL_FILTER_STR = (
    """gridpath_operational_type IN ('gen_commit_bin', 'gen_commit_lin')"""
)
HEAT_RATE_FILTER_STR = (
    """gridpath_operational_type IN ('gen_commit_bin', 'gen_commit_lin')"""
)
STOR_FILTER_STR = """gridpath_operational_type = 'stor'"""
VAR_GEN_FILTER_STR = """gridpath_operational_type IN ('gen_var', 'gen_var_must_take')"""
HYDRO_FILTER_STR = (
    """gridpath_operational_type IN ('gen_hydro', 'gen_hydro_must_take')"""
)
DISAGG_PROJECT_NAME_STR = (
    "plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', '_')"
)
AGG_PROJECT_NAME_STR = "DISTINCT agg_project || '_' || balancing_authority_code_eia"
