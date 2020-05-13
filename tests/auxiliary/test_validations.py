#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import numpy as np
import pandas as pd
import sqlite3
import unittest

import gridpath.auxiliary.validations as module_to_test


class TestAuxiliary(unittest.TestCase):
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

    def test_validate_nonnegatives(self):
        """

        :return:
        """
        df_columns = ["project", "load_point_fraction",
                      "average_heat_rate_mmbtu_per_mwh"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                columns=df_columns,
                data=[["gas_ct", 10, 10.5],
                      ["gas_ct", 20, 9],
                      ["coal_plant", 100, 10]
                      ]),
                "columns": ["load_point_fraction", "average_heat_rate_mmbtu_per_mwh"],
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
                "columns": ["load_point_fraction", "average_heat_rate_mmbtu_per_mwh"],
                "result": ["project(s) 'gas_ct, coal_plant': Expected 'load_point_fraction' >= 0",
                           "project(s) 'gas_ct': Expected 'average_heat_rate_mmbtu_per_mwh' >= 0"]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = module_to_test.validate_nonnegatives(
                df=test_cases[test_case]["df"],
                columns=test_cases[test_case]["columns"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_positives(self):
        cols = ["transmission_line", "reactance_ohms"]
        cols_to_check = ["reactance_ohms"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["tx1", 0.5]]),
                "result": [],
                },
            # Make sure invalid inputs are flagged
            2: {"df": pd.DataFrame(
                columns=cols,
                data=[["tx1", -0.5],
                      ["tx2", None]
                      ]),
                "result": ["transmission_line(s) 'tx1': Expected "
                           "'reactance_ohms' > 0"],
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = module_to_test.validate_positives(
                df=test_cases[test_case]["df"],
                columns=cols_to_check
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_pctfraction(self):
        df_columns = ["project", "horizon", "availability_derate"]
        cols_to_check = ["availability_derate"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                columns=df_columns,
                data=[["gas_ct", 201801, 1],
                      ["gas_ct", 201802, 0.9],
                      ["coal_plant", 201801, 0]
                      ]),
                "error": []
                },
            # Negative inputs are flagged
            2: {"df": pd.DataFrame(
                columns=df_columns,
                data=[["gas_ct", 201801, -1],
                      ["gas_ct", 201802, 0.9],
                      ["coal_plant", 201801, 0]
                      ]),
                "error": ["project(s) 'gas_ct': Expected 0 <= 'availability_derate' <= 1"]
                },
            # Inputs > 1 are flagged
            3: {"df": pd.DataFrame(
                columns=df_columns,
                data=[["gas_ct", 201801, 1],
                      ["gas_ct", 201802, 0.9],
                      ["coal_plant", 201801, -0.5]
                      ]),
                "error": ["project(s) 'coal_plant': Expected 0 <= 'availability_derate' <= 1"]
                },
            # Make sure multiple errors are flagged correctly
            4: {"df": pd.DataFrame(
                columns=df_columns,
                data=[["gas_ct", 201801, 1.5],
                      ["gas_ct", 201802, 0.9],
                      ["coal_plant", 201801, -0.5]
                      ]),
                "error": ["project(s) 'gas_ct, coal_plant': Expected 0 <= 'availability_derate' <= 1"]
                },
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["error"]
            actual_list = module_to_test.validate_pctfraction(
                df=test_cases[test_case]["df"],
                columns=cols_to_check
            )
            self.assertListEqual(expected_list, actual_list)

    def test_validate_pctfraction_nonzero(self):
        cols = ["project", "min_stable_level_fraction"]
        cols_to_check = ["min_stable_level_fraction"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"df": pd.DataFrame(
                    columns=cols,
                    data=[["gas_ct", 0.5]
                          ]),
                "result": [],
                },
            # Make sure invalid input is flagged
            2: {"df": pd.DataFrame(
                columns=cols,
                data=[["gas_ct1", 1.5],
                      ["gas_ct2", 0]
                      ]),
                "result": ["project(s) 'gas_ct1, gas_ct2': Expected 0 < 'min_stable_level_fraction' <= 1"],
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["result"]
            actual_list = module_to_test.validate_pctfraction_nonzero(
                df=test_cases[test_case]["df"],
                columns=cols_to_check
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
                "result": ["project(s) 'gas_ct2': Invalid entry for capacity_type"]
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

    def test_new_binary_build_inputs(self):
        cost_df_columns = ["project", "vintage", "lifetime_yrs",
                           "annualized_real_cost_per_mw_yr"]
        bld_size_df_columns = ["project", "gen_new_bin_build_size_mw"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"cost_df": pd.DataFrame(
                    columns=cost_df_columns,
                    data=[["gas_ct", 2018, 20, 100],
                          ["gas_ct", 2022, 20, 120]]),
                "bld_size_df": pd.DataFrame(
                    columns=bld_size_df_columns,
                    data=[["gas_ct", 1000]]),
                "prj_vintages": [("gas_ct", 2018), ("gas_ct", 2022)],
                "project_error": [],
                "cost_error": []
                },
            # Make sure missing bld size or cost is detected
            2: {"cost_df": pd.DataFrame(
                    columns=cost_df_columns,
                    data=[["gas_ct", 2018, 20, 100]]),
                "bld_size_df": pd.DataFrame(
                    columns=bld_size_df_columns,
                    data=[]),
                "prj_vintages": [("gas_ct", 2018), ("gas_ct", 2022)],
                "project_error": ["Missing build size inputs for project 'gas_ct'"],
                "cost_error": ["Missing cost inputs for project 'gas_ct', vintage '2022'"]
                }
        }

        for test_case in test_cases.keys():
            projects = [p[0] for p in test_cases[test_case]["prj_vintages"]]
            bld_size_projects = test_cases[test_case]["bld_size_df"]["project"]

            expected_list = test_cases[test_case]["project_error"]
            actual_list = module_to_test.validate_projects(
                list1=projects,
                list2=bld_size_projects
            )
            self.assertListEqual(expected_list, actual_list)

            expected_list = test_cases[test_case]["cost_error"]
            actual_list = module_to_test.validate_costs(
                cost_df=test_cases[test_case]["cost_df"],
                prj_vintages=test_cases[test_case]["prj_vintages"]
            )
            self.assertListEqual(expected_list, actual_list)

    def test_fuel_validations(self):
        prj_df_columns = ["project", "fuel"]
        fuels_df_columns = ["fuel", "co2_intensity_tons_per_mmbtu"]
        fuel_prices_df_columns = ["fuel", "period", "month",
                                  "fuel_price_per_mmbtu"]
        test_cases = {
            # Make sure correct inputs don't throw error
            1: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns,
                    data=[["gas_ct", "gas"], ["coal_plant", "coal"]]),
                "fuels_df": pd.DataFrame(
                    columns=fuels_df_columns,
                    data=[["gas", 0.4], ["coal", 0.8]]),
                "fuel_prices_df": pd.DataFrame(
                    columns=fuel_prices_df_columns,
                    data=[["gas", 2018, 1, 3], ["gas", 2018, 2, 4],
                          ["coal", 2018, 1, 2], ["coal", 2018, 2, 2]]),
                "periods_months": [(2018, 1), (2018, 2)],
                "fuel_project_error": [],
                "fuel_prices_error": []
                },
            # If a project's fuel in prj_df does not exist in the fuels_df,
            # there should be an error. Similarly, if a fuel price is missing
            # for a certain month/period, there should be an error.
            2: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns,
                    data=[["gas_ct", "invalid_fuel"], ["coal_plant", "coal"]]),
                "fuels_df": pd.DataFrame(
                    columns=fuels_df_columns,
                    data=[["gas", 0.4], ["coal", 0.8]]),
                "fuel_prices_df": pd.DataFrame(
                    columns=fuel_prices_df_columns,
                    data=[["gas", 2018, 1, 3],
                          ["coal", 2018, 1, 2], ["coal", 2018, 2, 2]]),
                "periods_months": [(2018, 1), (2018, 2)],
                "fuel_project_error": [
                    "Project(s) 'gas_ct': Specified fuel(s) 'invalid_fuel' do(es) not exist"],
                "fuel_prices_error": [
                    "Fuel 'gas': Missing price for period '2018', month '2'"]
                },
            # It's okay if there are more fuels and fuels prices specified than
            # needed for the active projects
            3: {"prj_df": pd.DataFrame(
                    columns=prj_df_columns,
                    data=[["gas_ct", "gas"]]),
                "fuels_df": pd.DataFrame(
                    columns=fuels_df_columns,
                    data=[["gas", 0.4], ["coal", 0.8]]),
                "fuel_prices_df": pd.DataFrame(
                    columns=fuel_prices_df_columns,
                    data=[["gas", 2018, 1, 3], ["gas", 2018, 2, 4],
                          ["coal", 2018, 1, 2], ["coal", 2018, 2, 2]]),
                "periods_months": [(2018, 1), (2018, 2)],
                "fuel_project_error": [],
                "fuel_prices_error": []
                },
            # Test for multiple errors in a column
            4: {"prj_df": pd.DataFrame(
                columns=prj_df_columns,
                data=[["gas_ct", "invalid_fuel1"], ["coal_plant", "invalid_fuel2"]]),
                "fuels_df": pd.DataFrame(
                    columns=fuels_df_columns,
                    data=[["gas", 0.4], ["coal", 0.8]]),
                "fuel_prices_df": pd.DataFrame(
                    columns=fuel_prices_df_columns,
                    data=[["gas", 2018, 1, 3],
                          ["coal", 2018, 1, 2]]),
                "periods_months": [(2018, 1), (2018, 2)],
                "fuel_project_error":
                    ["Project(s) 'gas_ct, coal_plant': Specified fuel(s) 'invalid_fuel1, invalid_fuel2' do(es) not exist"],
                "fuel_prices_error":
                    ["Fuel 'gas': Missing price for period '2018', month '2'",
                     "Fuel 'coal': Missing price for period '2018', month '2'"]
                }
        }

        for test_case in test_cases.keys():
            expected_list = test_cases[test_case]["fuel_project_error"]
            actual_list = module_to_test.validate_fuel_projects(
                prj_df=test_cases[test_case]["prj_df"],
                fuels_df=test_cases[test_case]["fuels_df"]
            )
            self.assertListEqual(expected_list, actual_list)

            expected_list = test_cases[test_case]["fuel_prices_error"]
            actual_list = module_to_test.validate_fuel_prices(
                fuels_df=test_cases[test_case]["fuels_df"],
                fuel_prices_df=test_cases[test_case]["fuel_prices_df"],
                periods_months=test_cases[test_case]["periods_months"]
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
