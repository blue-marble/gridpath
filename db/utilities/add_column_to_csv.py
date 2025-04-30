# Copyright 2016-2025 Blue Marble Analytics LLC.
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
import pandas as pd

# Add the base directory path here
BASE_DIR = ""

# Add the names of the files to update to this list
FILES = []

# Add the new column name, value, and position
NEW_COLUMN_NAME = str()
NEW_COLUMN_VALUE = None
NEW_COLUMN_POSITION = int()


def add_column_and_set_value(df, new_column_name, new_column_value, position=None):
    df[new_column_name] = new_column_value

    # Rearrange columns
    if position is not None:
        cols = df.columns.tolist()
        cols = cols[:position] + cols[-1:] + cols[position:-1]
        df = df[cols]

    return df


if __name__ == "__main__":
    for f in FILES:
        print(f)
        f_path = os.path.join(BASE_DIR, f)
        _df = pd.read_csv(f_path)

        updated_df = add_column_and_set_value(
            df=_df,
            new_column_name=NEW_COLUMN_NAME,
            new_column_value=NEW_COLUMN_VALUE,
            position=NEW_COLUMN_POSITION,
        )

        updated_df.to_csv(f_path, index=False)
