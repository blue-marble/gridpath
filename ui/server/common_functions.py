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

import glob
import os.path
import sys


def get_executable_path(script_name):
    """
    :param script_name: string; the name of the GridPath script
    :return: string; the path to the GridPath executable

    Get the entry point script path from the sys.executable. In Windows
    Anaconda environment, the Python executable and entry point scripts are
    not in the same directory; rather, the entry point scripts are in a
    directory called 'Scripts' inside the directory where the Python
    executable is located.
    """
    gridpath_executable = os.path.join(os.path.dirname(sys.executable), script_name)

    # If we can't find the GP script in the same directory as the system
    # executable, we'll try looking for it inside a 'Scripts' directory
    # This is where it is on Windows with an Anaconda environment
    # On Windows, we need to add (.exe), as the file will have a .exe extension
    # On Mac, an extension is not needed
    if not glob.glob("{}.exe".format(gridpath_executable)) and not glob.glob(
        gridpath_executable
    ):
        gridpath_executable = os.path.join(
            os.path.dirname(sys.executable), "Scripts", script_name
        )
        # If we still can't find it, raise an error
        if not glob.glob("{}.exe".format(gridpath_executable)) and not glob.glob(
            gridpath_executable
        ):
            raise OSError(
                "ERROR! {} is not the correct path for GridPath executable {}.".format(
                    gridpath_executable, script_name
                )
            )

    return gridpath_executable
