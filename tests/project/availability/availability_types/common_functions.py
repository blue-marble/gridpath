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

from collections import OrderedDict
import os.path
import pandas as pd


def get_endogenous_params(test_data_directory, param, project_subset):
    """
    :param test_data_directory:
    :param param:
    :param project_subset:
    :return:

    Get the correct subset dictionary for a param from
    project_availability_endogenous.tab.
    """
    all_dict = OrderedDict(
        pd.read_csv(
            os.path.join(
                test_data_directory, "inputs", "project_availability_endogenous.tab"
            ),
            sep="\t",
        )
        .set_index("project")
        .to_dict()[param]
        .items()
    )
    subset_dict = dict()
    for prj in all_dict:
        if prj in project_subset:
            subset_dict[prj] = all_dict[prj]

    return subset_dict
