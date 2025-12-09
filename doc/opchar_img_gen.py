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
This script generates the images (SVG and PNG) of the table of operational
characteristics with the corresponding project operational types for
inclusion into the documentation.

"""

import pandas as pd, numpy as np
import df2img

# df = pd.read_csv(
#     "../gridpath/project/operations/operational_types/opchar_param_requirements.csv",
#     na_filter=False,
# )
#
# d2i_tbl_hdr_dict = dict(
#     align="right", fill_color="blue", font_color="white", line_color="darkslategray"
# )
# d2i_tbl_cel_dict = dict(align="right", line_color="darkslategray")
#
# padding = 2  # Some elbow space for the values
# col_width_header = list(df.columns.str.len())
# col_width_values = [df[coll].map(len).max() for coll in df]
# col_width_both = [
#     max(one_col_width) + padding
#     for one_col_width in zip(col_width_header, col_width_values)
# ]
#
# fig = df2img.plot_dataframe(
#     df,
#     tbl_header=d2i_tbl_hdr_dict,
#     tbl_cells=d2i_tbl_cel_dict,
#     show_fig=False,
#     row_fill_color=("#ffffff", "#d7d8d6"),
#     print_index=False,
#     fig_size=(1800, 500),
#     col_width=tuple(col_width_both),
# )
#
# fig_table = fig.data[0]
# rr1, cc1 = np.where(df == "required")
# for validx in range(len(rr1)):
#     ra = rr1[validx]
#     ca = cc1[validx]
#     fig_table.cells.fill.color[ca][ra] = "#FF0000"
#
# rr2, cc2 = np.where(df == "optional")
# for validx in range(len(rr2)):
#     rb = rr2[validx]
#     cb = cc2[validx]
#     fig_table.cells.fill.color[cb][rb] = "#FFFF00"
#
# df2img.save_dataframe(fig=fig, filename="graphics/optype_opchar_matrix.png")
# df2img.save_dataframe(fig=fig, filename="graphics/optype_opchar_matrix.svg")
