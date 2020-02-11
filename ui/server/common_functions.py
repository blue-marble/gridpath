# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import os.path
import sys


def get_executable_path(script_name):
    """
    :param script_name: string; the name of the GridPath script
    :return: string; the path to the GridPath executable

    Get the entry point script path from the sys.executable (remove 'python'
    and add the script name)
    """
    chars_to_remove = 11 if os.name == "nt" else 7

    base_dir = os.path.basename(sys.executable[:-chars_to_remove])

    gridpath_executable = \
        os.path.join(
          sys.executable[:-chars_to_remove],
          "" if base_dir.lower() in ["scripts", "bin"] else "scripts",
          script_name
        )

    return gridpath_executable
