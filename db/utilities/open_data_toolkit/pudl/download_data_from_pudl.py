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
import gzip
import shutil
from argparse import ArgumentParser
import io
import os.path
import requests
import sys
import zipfile


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-z", "--zenodo_record", default=11292273)
    parser.add_argument(
        "-skip", "--skip_pudl_sqlite_download", default=False, action="store_true"
    )
    parser.add_argument(
        "-d",
        "--raw_data_directory",
        default="../../csvs_open_data/pudl_download",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_pudl_sqlite_from_pudl_zenodo(zenodo_record, download_directory):
    """ """
    url = f"https://zenodo.org/records/{str(zenodo_record)}/files/pudl.sqlite.gz?download=1"
    print("Downloading compressed pudl.sqlite...")
    pudl_request_content = requests.get(url, stream=True).content

    print("Extracting pudl.sqlite database...")
    with gzip.open(io.BytesIO(pudl_request_content), "rb") as f_in:
        with open(os.path.join(download_directory, "pudl.sqlite"), "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # For zip files, use the following
    # z = zipfile.ZipFile(io.BytesIO(pudl_request_content))
    # z.extractall(download_directory)


def get_parquet_file_from_pudl_zenodo(zenodo_record, filename, download_directory):
    """ """
    print(f"Downloading {filename}.parquet...")
    url = (
        f"https://zenodo.org/records/{zenodo_record}/files"
        f"/{filename}.parquet?download=1"
    )

    data = requests.get(url, stream=True).content

    with open(
        os.path.join(download_directory, f"{filename}.parquet"),
        "wb",
    ) as f:
        f.write(data)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not os.path.exists(parsed_args.raw_data_directory):
        os.makedirs(parsed_args.raw_data_directory)

    # Download the PUDL database
    if not parsed_args.skip_pudl_sqlite_download:
        get_pudl_sqlite_from_pudl_zenodo(
            zenodo_record=parsed_args.zenodo_record,
            download_directory=parsed_args.raw_data_directory,
        )

    # RA Toolkit profiles parquet file
    for filename in ["ra_toolkit_gen_profiles", "core_eia930__hourly_interchange"]:
        get_parquet_file_from_pudl_zenodo(
            zenodo_record=parsed_args.zenodo_record,
            download_directory=parsed_args.raw_data_directory,
            filename=filename,
        )


if __name__ == "__main__":
    main()
