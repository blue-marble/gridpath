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

"""
Solve from LP file with CPLEX and save GridPath-compatible solution file.
"""

import os.path
from subprocess import call
import sys

from gridpath.auxiliary.plugins.common_functions import parse_arguments


def main(args=None):
    if args is None:
        args = sys.argv[1:]
        parsed_args = parse_arguments(arguments=args)

        prob_sol_dir = parsed_args.problem_file_directory
        problem_file = parsed_args.problem_file_name

        call(
            """
        cplex -c read {problem} optimize write {solution}
        """.format(
                problem=os.path.join(prob_sol_dir, problem_file),
                solution=os.path.join(prob_sol_dir, "cplex_solution.sol"),
            ),
            shell=True,
        )


if __name__ == "__main__":
    main()
