#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import AbstractModel
import sqlite3
import unittest
import pandas as pd
import numpy as np

import gridpath.auxiliary.auxiliary as auxiliary_module_to_test


class TestAuxiliary(unittest.TestCase):
    """

    """
    def test_join_sets(self):
        """

        :return:
        """
        mod = AbstractModel()

        # If set list empty
        set_list_empty_actual = auxiliary_module_to_test.join_sets(mod, [])
        self.assertListEqual(set_list_empty_actual, [])

        # If single set in list
        mod.set1 = {1, 2, 3}
        set_list_single_set = ["set1"]
        single_set_expected = {1, 2, 3}
        single_set_actual = \
            auxiliary_module_to_test.join_sets(mod, set_list_single_set)
        self.assertSetEqual(single_set_expected, single_set_actual)

        # If more than one set
        mod.set2 = {4, 5, 6}
        set_list_two_sets = ["set1", "set2"]
        two_sets_joined_expected = {1, 2, 3, 4, 5, 6}
        two_sets_joined_actual = \
            auxiliary_module_to_test.join_sets(mod, set_list_two_sets)
        self.assertSetEqual(two_sets_joined_expected, two_sets_joined_actual)

    def test_check_list_has_single_item(self):
        """

        :return:
        """
        with self.assertRaises(ValueError):
            auxiliary_module_to_test.\
                check_list_has_single_item([1, 2], "Error_Msg")

    def test_find_item_position(self):
        """

        :return:
        """
        l = [1, 2, 3]
        self.assertEqual([0],
                         auxiliary_module_to_test.
                         find_list_item_position(l=l, item=1)
                         )

        self.assertEqual([1],
                         auxiliary_module_to_test.
                         find_list_item_position(l=l, item=2)
                         )

        self.assertEqual([2],
                         auxiliary_module_to_test.
                         find_list_item_position(l=l, item=3)
                         )

    def test_check_list_items_are_unique(self):
        """

        :return:
        """
        with self.assertRaises(ValueError):
            auxiliary_module_to_test.check_list_items_are_unique([1, 1])

    def test_is_number(self):
        """

        :return:
        """
        self.assertEqual(True, auxiliary_module_to_test.is_number(1))
        self.assertEqual(True, auxiliary_module_to_test.is_number(100.5))
        self.assertEqual(False, auxiliary_module_to_test.is_number("string"))

    def test_get_expected_dtypes(self):
        """

        :return:
        """

        # Setup
        conn = sqlite3.connect(":memory:")
        conn.execute(
            """CREATE TABLE table1 (
            col1 INTEGER, col2 FLOAT, col3 DOUBLE, col4 TEXT, col5 VARCHAR(32)
            );"""
        )
        conn.execute(
            """CREATE TABLE table2 (
            col1 TEXT, col6 VARCHAR(64), col7 VARCHAR(128)
            );"""
        )
        conn.commit()

        # Test dict gets created properly for one table
        expected_dict = {
            "col1": "numeric",
            "col2": "numeric",
            "col3": "numeric",
            "col4": "string",
            "col5": "string"
        }
        actual_dict = auxiliary_module_to_test.get_expected_dtypes(
            conn, ["table1"]
        )
        self.assertDictEqual(expected_dict, actual_dict)

        # Test dict gets created properly for multiple tables
        expected_dict = {
            "col1": "string",
            "col2": "numeric",
            "col3": "numeric",
            "col4": "string",
            "col5": "string",
            "col6": "string",
            "col7": "string"
        }
        actual_dict = auxiliary_module_to_test.get_expected_dtypes(
            conn, ["table1", "table2"]
        )
        self.assertDictEqual(expected_dict, actual_dict)

        # Tear down: close connection
        conn.close()

    def test_check_dtypes(self):
        """

        :return:
        """
        df_columns = ["project", "capacity"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["gas_ct", 10], ["coal_plant", 20]]),
                "expected_dtypes": {
                    "project": "string",
                    "capacity": "numeric"},
                "result": ([], [])
                },
            # Test invalid string column
            2: {"df": pd.DataFrame(
                columns=df_columns,
                data=[["gas_ct", 10], ["coal_plant", "string"]]),
                "expected_dtypes": {
                    "project": "string",
                    "capacity": "numeric"},
                "result": (
                    ["Invalid data type for column 'capacity'; expected numeric"],
                    ["capacity"]
                )},
            # Test invalid numeric column
            3: {"df": pd.DataFrame(
                columns=df_columns,
                data=[[1, 10], [1, 20]]),
                "expected_dtypes": {
                    "project": "string",
                    "capacity": "numeric"},
                "result": (
                    ["Invalid data type for column 'project'; expected string"],
                    ["project"]
                )},
            # If at least one string in the column, pandas will convert
            # all column data to string so there will be no error
            4: {"df": pd.DataFrame(
                columns=df_columns,
                data=[["gas_ct", 10], [1, 20]]),
                "expected_dtypes": {
                    "project": "string",
                    "capacity": "numeric"},
                "result": ([], [])
                },
            # Columns with all None are ignored
            5: {"df": pd.DataFrame(
                columns=df_columns,
                data=[[None, 10], [None, 20]]),
                "expected_dtypes": {
                    "project": "string",
                    "capacity": "numeric"},
                "result": ([], [])
                },
            # Columns with all NaN are ignored
            6: {"df": pd.DataFrame(
                columns=df_columns,
                data=[[np.nan, 10], [np.nan, 20]]),
                "expected_dtypes": {
                    "project": "string",
                    "capacity": "numeric"},
                "result": ([], [])
                },
            # Columns with some None are not ignored
            7: {"df": pd.DataFrame(
                columns=df_columns,
                data=[[10, 10], [None, 20]]),
                "expected_dtypes": {
                    "project": "string",
                    "capacity": "numeric"},
                "result": (
                    ["Invalid data type for column 'project'; expected string"],
                    ["project"]
                )},
            # Test multiple error columns
            8: {"df": pd.DataFrame(
                columns=df_columns,
                data=[[10, "string"], [10, "string"]]),
                "expected_dtypes": {
                    "project": "string",
                    "capacity": "numeric"},
                "result": (
                    ["Invalid data type for column 'project'; expected string",
                     "Invalid data type for column 'capacity'; expected numeric"],
                    ["project", "capacity"]
                )}
        }

        for test_case in test_cases.keys():
            expected_tuple = test_cases[test_case]["result"]
            actual_tuple = auxiliary_module_to_test.check_dtypes(
                df=test_cases[test_case]["df"],
                expected_dtypes=test_cases[test_case]["expected_dtypes"]
            )
            self.assertTupleEqual(expected_tuple, actual_tuple)

    def test_check_column_sign_positive(self):
        """

        :return:
        """
        df_columns = ["project", "load_point_mw",
                      "average_heat_rate_mmbtu_per_mwh"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                columns=df_columns,
                data=[["gas_ct", 10, 10.5],
                      ["gas_ct", 20, 9],
                      ["coal_plant", 100, 10]
                      ]),
                "columns": ["load_point_mw", "average_heat_rate_mmbtu_per_mwh"],
                "result": []
                },
            # Sign errors are flagged; Errors are grouped by column. If >1 error
            # in different columns, a separate error msgs will be created
            2: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["gas_ct", 10, -10.5],
                          ["gas_ct", -20, 9],
                          ["coal_plant", -100, 10]
                          ]),
                "columns": ["load_point_mw", "average_heat_rate_mmbtu_per_mwh"],
                "result": ["Project(s) 'gas_ct, coal_plant': Expected 'load_point_mw' >= 0",
                           "Project(s) 'gas_ct': Expected 'average_heat_rate_mmbtu_per_mwh' >= 0"]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = auxiliary_module_to_test.check_column_sign_positive(
                df=test_cases[test_case]["df"],
                columns=test_cases[test_case]["columns"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_check_req_prj_columns(self):
        """

        :return:
        """

        df_columns = ["project", "min_stable_level", "unit_size_mw",
                      "startup_cost_per_mw", "shutdown_cost_per_mw"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["nuclear", 0.5, 100, None, None]]),
                "columns": ["min_stable_level", "unit_size_mw"],
                "required": True,
                "category": "Always_on",
                "result": []
                },
            # Make sure missing required inputs are flagged
            2: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["nuclear", None, 100, None, None]]),
                "columns": ["min_stable_level", "unit_size_mw"],
                "required": True,
                "category": "Always_on",
                "result": ["Project(s) 'nuclear'; Always_on should have inputs for 'min_stable_level'"]
                },
            # Make sure incompatible inputs are flagged
            3: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["nuclear", 0.5, 100, 1000, None]]),
                "columns": ["startup_cost_per_mw", "shutdown_cost_per_mw"],
                "required": False,
                "category": "Always_on",
                "result": ["Project(s) 'nuclear'; Always_on should not have inputs for 'startup_cost_per_mw'"]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = auxiliary_module_to_test.check_req_prj_columns(
                df=test_cases[test_case]["df"],
                columns=test_cases[test_case]["columns"],
                required=test_cases[test_case]["required"],
                category=test_cases[test_case]["category"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_check_prj_column(self):
        """

        :return:
        """

        cols = ["project", "capacity_type"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                columns=cols,
                data=[["gas_ct", "gen_new_lin"]
                      ]),
                "column": "capacity_type",
                "valids": ["gen_new_lin"],
                "result": []
                },
            # Make sure invalid column entry is flagged
            2: {"df": pd.DataFrame(
                columns=cols,
                data=[["gas_ct1", "gen_new_lin"],
                      ["gas_ct2", "invalid_cap_type"],
                      ["storage_plant", "stor_new_lin"]
                      ]),
                "column": "capacity_type",
                "valids": ["gen_new_lin", "stor_new_lin"],
                "result": ["Project(s) 'gas_ct2': Invalid entry for capacity_type"]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = auxiliary_module_to_test.check_prj_column(
                df=test_cases[test_case]["df"],
                column=test_cases[test_case]["column"],
                valids=test_cases[test_case]["valids"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_check_constant_heat_rate(self):
        """

        :return:
        """

        df_columns = ["project", "load_point_mw"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["nuclear", 100]]),
                "op_type": "Always_on",
                "result": []
                },
            # Make sure varying heat rates (>1 load point) is flagged
            2: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["nuclear", 100],
                          ["nuclear", 200],
                          ["gas_ct", 10]
                          ]),
                "op_type": "Always_on",
                "result": ["Project(s) 'nuclear': Always_on should have only 1 load point"]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = auxiliary_module_to_test.check_constant_heat_rate(
                df=test_cases[test_case]["df"],
                op_type=test_cases[test_case]["op_type"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_check_projects_for_reserves(self):
        """

        :return:
        """

        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"projects_op_type": ["project1", "project2"],
                "projects_w_ba": ["project3", "project4"],
                "operational_type": "gen_must_run",
                "reserve": "regulation_up",
                "result": []
                },
            # Make sure invalid projects are flagged
            2: {"projects_op_type": ["project1", "project2"],
                "projects_w_ba": ["project2", "project3"],
                "operational_type": "gen_must_run",
                "reserve": "regulation_up",
                "result": ["Project(s) 'project2'; gen_must_run cannot provide regulation_up"]
                },
            # Make sure multiple invalid projects are flagged correctly
            3: {"projects_op_type": ["project1", "project2"],
                "projects_w_ba": ["project1", "project2", "project3"],
                "operational_type": "gen_must_run",
                "reserve": "regulation_up",
                "result": [
                    "Project(s) 'project1, project2'; gen_must_run cannot provide regulation_up"]
                },
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = auxiliary_module_to_test.check_projects_for_reserves(
                projects_op_type=test_cases[test_case]["projects_op_type"],
                projects_w_ba=test_cases[test_case]["projects_w_ba"],
                operational_type=test_cases[test_case]["operational_type"],
                reserve=test_cases[test_case]["reserve"],
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_startup_shutdown_rate_inputs(self):
        """
        Test input validation for startup and shutdown rates
        :return:
        """

        prj_df_columns = ["project", "operational_type", "min_stable_level"]
        su_df_columns = ["project", "down_time_cutoff_hours",
                         "startup_plus_ramp_up_rate"]
        test_cases = {
            # Make sure a case with only basic inputs doesn't throw errors
            1: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns,
                    data=[["ccgt", "gen_commit_bin", 0.6]]),
                "su_df": pd.DataFrame(columns=su_df_columns),
                "result": []
                },
            # Make sure correct inputs don't throw errors
            2: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns + ["min_down_time_hours",
                                          "shutdown_plus_ramp_down_rate",
                                          "startup_fuel_mmbtu_per_mw"],
                    data=[["ccgt", "gen_commit_bin", 0.6, 8, 0.00334, 0]]),
                "su_df": pd.DataFrame(
                    columns=su_df_columns,
                    data=[["ccgt", 8, 0.00334],
                          ["ccgt", 12, 0.002]]),
                "result": []
                },
            # Make sure too short min down time is flagged
            3: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns + ["min_down_time_hours",
                                          "shutdown_plus_ramp_down_rate",
                                          "startup_fuel_mmbtu_per_mw"],
                    data=[["ccgt", "gen_commit_bin", 0.6, 4, 0.00334, 0]]),
                "su_df": pd.DataFrame(
                    columns=su_df_columns,
                    data=[["ccgt", 4, 0.00334],
                          ["ccgt", 12, 0.002]]),
                "result": ["Project(s) 'ccgt': Startup ramp duration plus shutdown ramp duration "
                           "should be less than the minimum down time. Make sure the minimum "
                           "down time is long enough to fit the (coldest) "
                           "trajectories!"]
                },
            # Make sure multiple projects get flagged correctly
            4: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns + ["min_down_time_hours",
                                          "shutdown_plus_ramp_down_rate",
                                          "startup_fuel_mmbtu_per_mw"],
                    data=[["ccgt", "gen_commit_bin", 0.6, 4, 0.00334, 0],
                          ["ccgt2", "gen_commit_bin", 0.6, 4, 0.00334, 0]]),
                "su_df": pd.DataFrame(
                    columns=su_df_columns,
                    data=[["ccgt", 4, 0.00334],
                          ["ccgt2", 4, 0.00334]]),
                "result": ["Project(s) 'ccgt, ccgt2': Startup ramp duration plus shutdown ramp duration"
                           " should be less than the minimum down time. Make sure the minimum"
                           " down time is long enough to fit the (coldest) "
                           "trajectories!"]
                },
            # Make sure a startup trajectory without min down time gets flagged
            5: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns,
                    data=[["ccgt", "gen_commit_bin", 0.6]]),
                "su_df": pd.DataFrame(
                    columns=su_df_columns,
                    data=[["ccgt", 8, 0.00334]]),
                "result": [
                    "Project(s) 'ccgt': Startup ramp duration plus shutdown ramp duration"
                    " should be less than the minimum down time. Make sure the minimum"
                    " down time is long enough to fit the (coldest) trajectories!",
                    "Project(s) 'ccgt': down_time_cutoff_hours of hottest start should "
                    "match project's minimum_down_time_hours. If there is no minimum "
                    "down time, set cutoff to zero."]
                },
            # Make sure quick-start units don't get flagged even if no min down
            # time provided (defaults to zero)
            6: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns,
                    data=[["ccgt", "gen_commit_bin", 0.6]]),
                "su_df": pd.DataFrame(
                    columns=su_df_columns,
                    data=[["ccgt", 0, 0.012]]),
                "result": []
                },
            # Make sure startup fuel + trajectory combination is flagged
            7: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns + ["min_down_time_hours",
                                          "shutdown_plus_ramp_down_rate",
                                          "startup_fuel_mmbtu_per_mw"],
                    data=[["ccgt", "gen_commit_bin", 0.6, 8, 0.00334, 1]]),
                "su_df": pd.DataFrame(
                    columns=su_df_columns,
                    data=[["ccgt", 8, 0.00334]]),
                "result": ["Project(s) 'ccgt': Cannot have both startup_fuel inputs and a startup "
                           "trajectory that takes multiple timepoints as this will double "
                           "count startup fuel consumption. Please adjust startup ramp rate or"
                           " startup fuel consumption inputs"]
                },
            # Make sure ramp rates decrease with increasing down time cutoff
            8: {"prj_df": pd.DataFrame(
                columns=prj_df_columns + ["min_down_time_hours",
                                          "shutdown_plus_ramp_down_rate",
                                          "startup_fuel_mmbtu_per_mw"],
                data=[["ccgt", "gen_commit_bin", 0.6, 8, 0.00334, 0]]),
                "su_df": pd.DataFrame(
                    columns=su_df_columns,
                    data=[["ccgt", 8, 0.00334],
                          ["ccgt", 12, 0.005]]),
                "result": [
                    "Project(s) 'ccgt': Startup ramp rate should decrease with "
                    "increasing down time cutoff (colder starts are slower)."]
            },

            # TODO: there are more situations to test (see aux #4 and #5)
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = auxiliary_module_to_test.\
                validate_startup_shutdown_rate_inputs(
                    prj_df=test_cases[test_case]["prj_df"],
                    su_df=test_cases[test_case]["su_df"],
                    hrs_in_tmp=1
                )
            self.assertListEqual(expected_list, actual_list)


if __name__ == "__main__":
    unittest.main()
