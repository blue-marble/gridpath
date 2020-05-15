#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import numpy as np
import pandas as pd
import sqlite3
import unittest

import gridpath.auxiliary.validations as module_to_test


class TestValidations(unittest.TestCase):
    """

    """

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
        actual_dict = module_to_test.get_expected_dtypes(
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
        actual_dict = module_to_test.get_expected_dtypes(
            conn, ["table1", "table2"]
        )
        self.assertDictEqual(expected_dict, actual_dict)

        # Tear down: close connection
        conn.close()

    def test_validate_dtypes(self):
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
            actual_tuple = module_to_test.validate_dtypes(
                df=test_cases[test_case]["df"],
                expected_dtypes=test_cases[test_case]["expected_dtypes"]
            )
            self.assertTupleEqual(expected_tuple, actual_tuple)

    def test_validate_signs(self):
        """

        :return:
        """
        cols = ["project", "load_point_fraction",
                "average_heat_rate_mmbtu_per_mwh"]
        cols_to_check = ["load_point_fraction",
                         "average_heat_rate_mmbtu_per_mwh"]
        test_cases = {
            # Make sure correct nonnegative inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 10, 10.5],
                          ["gas_ct", 20, 9],
                          ["coal_plant", 100, 10]
                          ]),
                "sign": "nonnegative",
                "result": []
                },
            # Make sure nonnegative errors are flagged; Errors are grouped by
            # column. If >1 error in different columns, a separate error
            # msgs will be created.
            2: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 10, -10.5],
                          ["gas_ct", -20, 9],
                          ["coal_plant", -100, 10]
                          ]),
                "sign": "nonnegative",
                "result": ["project(s) 'gas_ct, coal_plant': Expected 'load_point_fraction' >= 0",
                           "project(s) 'gas_ct': Expected 'average_heat_rate_mmbtu_per_mwh' >= 0"]
                },
            # Make sure correct positive inputs don't throw error
            3: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 10, 10.5]]),
                "sign": "positive",
                "result": []
                },
            # Make sure positive errors are flagged
            4: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 10, 0]]),
                "sign": "positive",
                "result": ["project(s) 'gas_ct': Expected 'average_heat_rate_mmbtu_per_mwh' > 0"]
                },
            # Make sure correct pctfraction_nonzero inputs don't throw error
            5: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 0.2, 0.5]]),
                "sign": "pctfraction_nonzero",
                "result": []
                },
            # Make sure pctfraction_nonzero errors are flagged
            6: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct1", 0.2, 1.5],
                          ["gas_ct2", 0.2, 0]
                          ]),
                "sign": "pctfraction_nonzero",
                "result": ["project(s) 'gas_ct1, gas_ct2': Expected 'average_heat_rate_mmbtu_per_mwh' within (0, 1]"]
                },
            # Make sure correct pctfraction inputs don't throw error
            7: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 0.2, 1],
                          ["gas_ct", 0.5, 0.9],
                          ["coal_plant", 1, 0]
                          ]),
                "sign": "pctfraction",
                "result": []
                },
            # Make sure negative inputs are flagged for pctraction
            8: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 0.2, -1],
                          ["gas_ct", 0.5, 0.9],
                          ["coal_plant", 1, 0]
                          ]),
                "sign": "pctfraction",
                "result": ["project(s) 'gas_ct': Expected 'average_heat_rate_mmbtu_per_mwh' within [0, 1]"]
                },
            # Make sure inputs > 1 are flagged for pctfraction
            9: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 0.2, 1],
                          ["gas_ct", 0.5, 0.9],
                          ["coal_plant", 1, 1.9]
                          ]),
                "sign": "pctfraction",
                "result": ["project(s) 'coal_plant': Expected 'average_heat_rate_mmbtu_per_mwh' within [0, 1]"]
                },
            # Make sure multiple pctfraction errors are flagged
            10: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 0.2, -1],
                          ["gas_ct", 0.5, 0.9],
                          ["coal_plant", 1, 1.9]
                          ]),
                 "sign": "pctfraction",
                 "result": ["project(s) 'gas_ct, coal_plant': Expected 'average_heat_rate_mmbtu_per_mwh' within [0, 1]"]
                 },
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = module_to_test.validate_signs(
                df=test_cases[test_case]["df"],
                columns=cols_to_check,
                sign=test_cases[test_case]["sign"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_req_cols(self):
        """

        :return:
        """

        df_columns = ["project", "min_stable_level_fraction", "unit_size_mw",
                      "startup_cost_per_mw", "shutdown_cost_per_mw"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["nuclear", 0.5, 100, None, None]]),
                "columns": ["min_stable_level_fraction", "unit_size_mw"],
                "required": True,
                "category": "Always_on",
                "result": []
                },
            # Make sure missing required inputs are flagged
            2: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["nuclear", None, 100, None, None]]),
                "columns": ["min_stable_level_fraction", "unit_size_mw"],
                "required": True,
                "category": "Always_on",
                "result": ["project(s) 'nuclear'; Always_on should have "
                           "inputs for 'min_stable_level_fraction'"]
                },
            # Make sure incompatible inputs are flagged
            3: {"df": pd.DataFrame(
                    columns=df_columns,
                    data=[["nuclear", 0.5, 100, 1000, None]]),
                "columns": ["startup_cost_per_mw", "shutdown_cost_per_mw"],
                "required": False,
                "category": "Always_on",
                "result": ["project(s) 'nuclear'; Always_on should not have inputs for 'startup_cost_per_mw'"]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = module_to_test.validate_req_cols(
                df=test_cases[test_case]["df"],
                columns=test_cases[test_case]["columns"],
                required=test_cases[test_case]["required"],
                category=test_cases[test_case]["category"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_column(self):
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
                "result": ["project(s) 'gas_ct2': Invalid entry for "
                           "capacity_type. Valid options are ['gen_new_lin', "
                           "'stor_new_lin']."]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = module_to_test.validate_column(
                df=test_cases[test_case]["df"],
                column=test_cases[test_case]["column"],
                valids=test_cases[test_case]["valids"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_req_idxs(self):
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"required_idxs": ["gas_ct"],
                "actual_idxs": ["gas_ct", "coal_plant"],
                "idx_label": "project",
                "result": [],
                },
            # Make sure invalid inputs are detected
            2: {"required_idxs": ["gas_ct"],
                "actual_idxs": [],
                "idx_label": "project",
                "result": ["Missing inputs for project: ['gas_ct']"]
                },
            # Make sure invalid tuple indexes are properly detected
            3: {"required_idxs": [("gas_ct", 2020)],
                "actual_idxs": [],
                "idx_label": "(project, period)",
                "result": ["Missing inputs for (project, period): [('gas_ct', 2020)]"]
                },
            # Make sure multiple invalid tuple indexes are properly detected
            # (results are sorted!)
            4: {"required_idxs": [("gas_ct", 2020),
                                  ("coal_plant", 2020)],
                "actual_idxs": [],
                "idx_label": "(project, period)",
                "result": ["Missing inputs for (project, period): [('coal_plant', 2020), ('gas_ct', 2020)]"]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = module_to_test.validate_req_idxs(
                required_idxs=test_cases[test_case]["required_idxs"],
                actual_idxs=test_cases[test_case]["actual_idxs"],
                idx_label=test_cases[test_case]["idx_label"],
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_op_cap_combos(self):
        cols1 = ["project", "capacity_type", "operational_type"]
        cols2 = ["transmission_line", "capacity_type", "operational_type"]
        test_cases = {
            # Make sure correct inputs don't throw error for projcts
            1: {"df": pd.DataFrame(
                    columns=cols1,
                    data=[["gas_ct", "gen_new_lin",
                           "gen_commit_cap"]
                          ]),
                "invalid_combos": [("invalid1", "invalid2")],
                "combo_error": [],
                },
            # Make sure invalid combo is flagged for projects
            2: {"df": pd.DataFrame(
                columns=cols1,
                data=[["gas_ct1", "cap1", "op2"],
                      ["gas_ct2", "cap1", "op3"]
                      ]),
                "invalid_combos": [("cap1", "op2")],
                "combo_error": ["project(s) 'gas_ct1': capacity type 'cap1' "
                                "and operational type 'op2' cannot be "
                                "combined"],
                },
            # Make sure correct inputs don't throw error for tx lines
            3: {"df": pd.DataFrame(
                    columns=cols2,
                    data=[["tx1", "tx_spec", "tx_simple"]
                          ]),
                "invalid_combos": [("invalid1", "invalid2")],
                "combo_error": [],
                },
            # Make sure invalid combos are flagged for tx lines
            4: {"df": pd.DataFrame(
                columns=cols2,
                data=[["tx1", "new_build", "tx_dcopf"],
                      ["tx2", "new_build", "tx_simple"]
                      ]),
                "invalid_combos": [("new_build", "tx_dcopf")],
                "combo_error": ["transmission_line(s) 'tx1': capacity type "
                                "'new_build' and operational type 'tx_dcopf' "
                                "cannot be combined"],
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["combo_error"]
            actual_list = module_to_test.validate_op_cap_combos(
                df=test_cases[test_case]["df"],
                invalid_combos=test_cases[test_case]["invalid_combos"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_heat_rate_validations(self):
        hr_columns = ["project", "fuel", "heat_rate_curves_scenario_id",
                      "period",
                      "load_point_fraction", "average_heat_rate_mmbtu_per_mwh"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"hr_df": pd.DataFrame(
                    columns=hr_columns,
                    data=[["gas_ct", "gas", 1, 2020, 10, 10.5],
                          ["gas_ct", "gas", 1, 2020, 20, 9],
                          ["coal_plant", "coal", 1, 2020, 100, 10]
                          ]),
                "fuel_vs_hr_error": [],
                "hr_curves_error": []
                },
            # Check fuel vs heat rate curve errors
            2: {"hr_df": pd.DataFrame(
                columns=hr_columns,
                data=[["gas_ct", "gas", None, None, None, None],
                      ["coal_plant", None, 1, 2020, 100, 10]
                      ]),
                "fuel_vs_hr_error": ["Project(s) 'gas_ct': Missing heat_rate_curves_scenario_id",
                                     "Project(s) 'coal_plant': No fuel specified so no heat rate expected"],
                "hr_curves_error": []
                },
            # Check heat rate curves validations
            3: {"hr_df": pd.DataFrame(
                columns=hr_columns,
                data=[["gas_ct1", "gas", 1, None, None, None],
                      ["gas_ct2", "gas", 1, 2020, 10, 11],
                      ["gas_ct2", "gas", 1, 2020, 10, 12],
                      ["gas_ct3", "gas", 1, 2020, 10, 11],
                      ["gas_ct3", "gas", 1, 2020, 20, 5],
                      ["gas_ct4", "gas", 1, 2020, 10, 11],
                      ["gas_ct4", "gas", 1, 2020, 20, 10],
                      ["gas_ct4", "gas", 1, 2020, 30, 9]
                      ]),
                "fuel_vs_hr_error": [],
                "hr_curves_error": ["Project(s) 'gas_ct1': Expected at least one load point",
                                    "Project(s) 'gas_ct2': load points can not be identical",
                                    "Project(s) 'gas_ct3': Total fuel burn should increase with increasing load",
                                    "Project(s) 'gas_ct4': Fuel burn should be convex, i.e. marginal heat rate should increase with increading load"]
                },

        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["fuel_vs_hr_error"]
            actual_list = module_to_test.validate_fuel_vs_heat_rates(
                hr_df=test_cases[test_case]["hr_df"]
            )
            self.assertListEqual(expected_list, actual_list)

            expected_list = test_cases[test_case]["hr_curves_error"]
            actual_list = module_to_test.validate_heat_rate_curves(
                hr_df=test_cases[test_case]["hr_df"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_startup_shutdown_rate_inputs(self):
        """
        Test input validation for startup and shutdown rates
        :return:
        """

        prj_df_columns = ["project", "operational_type",
                          "min_stable_level_fraction"]
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
            actual_list = module_to_test.validate_startup_shutdown_rate_inputs(
                prj_df=test_cases[test_case]["prj_df"],
                su_df=test_cases[test_case]["su_df"],
                hrs_in_tmp=1
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_constant_heat_rate(self):
        """

        :return:
        """

        df_columns = ["project", "load_point_fraction"]
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
            actual_list = module_to_test.validate_constant_heat_rate(
                df=test_cases[test_case]["df"],
                op_type=test_cases[test_case]["op_type"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_projects_for_reserves(self):
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
            actual_list = module_to_test.validate_projects_for_reserves(
                projects_op_type=test_cases[test_case]["projects_op_type"],
                projects_w_ba=test_cases[test_case]["projects_w_ba"],
                operational_type=test_cases[test_case]["operational_type"],
                reserve=test_cases[test_case]["reserve"],
            )
            self.assertListEqual(expected_list, actual_list)


if __name__ == "__main__":
    unittest.main()
