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

import os.path
import sys


def get_executable_path(script_name):
    """
    :param script_name: string; the name of the GridPath script
    :return: string; the path to the GridPath executable

    Get the entry point script path from the sys.executable. On Windows,
    the GridPath scripts are located in a 'Scripts' directory within the base
    directory of the Python executable; on Mac, the Python executable and
    the GridPath script are in the same directory.
    """
    gridpath_executable = os.path.join(
          os.path.dirname(sys.executable),
          "Scripts" if os.name == "nt" else "",
          script_name
        )

    return gridpath_executable
