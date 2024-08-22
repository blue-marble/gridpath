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


def get_all_links_sql(region):
    all_links_sql = f"""
                SELECT DISTINCT balancing_authority_code_eia, balancing_authority_code_adjacent_eia
                FROM raw_data_eia930_hourly_interchange
                WHERE balancing_authority_code_eia in (
                SELECT baa FROM (
                    SELECT DISTINCT baa from (
                        SELECT DISTINCT balancing_authority_code_eia as baa
                        FROM raw_data_eia930_hourly_interchange
                        UNION
                        SELECT DISTINCT balancing_authority_code_adjacent_eia as ba
                        FROM raw_data_eia930_hourly_interchange
                        )
                    )
                    LEFT OUTER JOIN
                    aux_baa_key
                    USING (baa)
                WHERE region = '{region}'
                )
                AND
                balancing_authority_code_adjacent_eia in (
                SELECT baa FROM (
                    SELECT DISTINCT baa from (
                        SELECT DISTINCT balancing_authority_code_eia as baa
                        FROM raw_data_eia930_hourly_interchange
                        UNION
                        SELECT DISTINCT balancing_authority_code_adjacent_eia as ba
                        FROM raw_data_eia930_hourly_interchange
                        )
                    )
                    LEFT OUTER JOIN
                    aux_baa_key
                    USING (baa)
                WHERE region = '{region}'
                )
                ;
                """

    return all_links_sql
