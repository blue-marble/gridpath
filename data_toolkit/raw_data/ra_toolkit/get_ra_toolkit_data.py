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


"""
Download RA Toolkit data from Google Drive.
"""
from argparse import ArgumentParser
import gdown
import os.path
import sys

from db.utilities.common_functions import confirm

RAW_DATA_DIRECTORY_DEFAULT = "./raw_data"


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument(
        "-d",
        "--raw_data_directory",
        default=RAW_DATA_DIRECTORY_DEFAULT,
        help=f"Defaults to {RAW_DATA_DIRECTORY_DEFAULT}",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def download_file(gdrive_file_id, filename, download_directory):
    """ """
    proceed = True
    filepath = os.path.join(download_directory, filename)
    if os.path.exists(filepath):
        proceed = confirm(
            f"WARNING: The file {filepath} already exists. Downloading "
            f"the data again will overwrite the previous file. Are you sure?"
        )

    if proceed:
        print(f"Downloading {filename}...")
        gdrive_file_id = f"https://drive.google.com/uc?id={gdrive_file_id}"
        gdown.download(gdrive_file_id, filepath, quiet=False)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    os.makedirs(parsed_args.raw_data_directory, exist_ok=True)

    file_dict = {
        "ra_toolkit_hydro.csv": "1k5FtwE44avnicAXSHbo1twR7zwh2hjo9",
        "ra_toolkit_load.csv": "1k4JdsUhMyZg_OQR5rvteg-tg-s2kS8Za",
    }
    for filename in file_dict.keys():
        download_file(
            download_directory=parsed_args.raw_data_directory,
            filename=filename,
            gdrive_file_id=file_dict[filename],
        )


if __name__ == "__main__":
    main()
