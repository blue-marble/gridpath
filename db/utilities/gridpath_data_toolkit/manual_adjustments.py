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

from argparse import ArgumentParser
import os.path
import shutil
import sys


VAR_ID_DEFAULT = 1
VAR_NAME_DEFAULT = "MANUAL"
STAGE_ID_DEFAULT = 1


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-out_dir", "--output_directory")
    parser.add_argument(
        "-id",
        "--variable_generator_profile_scenario_id",
        default=VAR_ID_DEFAULT,
        help=f"Defaults to {VAR_ID_DEFAULT}.",
    )
    parser.add_argument(
        "-name",
        "--variable_generator_profile_scenario_name",
        default=VAR_NAME_DEFAULT,
        help=f"Defaults to '{VAR_NAME_DEFAULT}'.",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing CSV files.",
    )

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def make_copy_wind_profiles(output_directory, profile_id, profile_name, overwrite):
    copy_from_dict = {"NEVP": "SPPC", "PGE": "BPAT", "SRP": "AZPS", "WAUW": "NWMT"}

    for ba in copy_from_dict.keys():
        copy_ba = copy_from_dict[ba]

        file_to_copy = os.path.join(
            output_directory,
            f"Wind_{copy_ba}-{profile_id}-{profile_name}.csv",
        )

        new_file = os.path.join(
            output_directory,
            f"Wind_{ba}-{profile_id}-{profile_name}-MANUAL_copy_from_{copy_ba}.csv",
        )

        shutil.copyfile(file_to_copy, new_file)


def main(args=None):
    print("Making manual adjustments")
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args)

    output_directory = parsed_args.output_directory
    profile_id = parsed_args.variable_generator_profile_scenario_id
    profile_name = parsed_args.variable_generator_profile_scenario_name
    overwrite = parsed_args.overwrite

    make_copy_wind_profiles(
        output_directory=output_directory,
        profile_id=profile_id,
        profile_name=profile_name,
        overwrite=overwrite,
    )


if __name__ == "__main__":
    main()
