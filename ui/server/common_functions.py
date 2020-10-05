# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

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
