#!/usr/bin/env python

"""
Describe operational constraints on the generation infrastructure.
"""
import csv
import os.path
import pandas as pd
from pyomo.environ import Expression, value

from modules.auxiliary.dynamic_components import \
    required_operational_modules, load_balance_production_components, \
    required_reserve_modules
from modules.auxiliary.auxiliary import make_project_time_var_df, \
    load_operational_type_modules, load_reserve_type_modules, \
    check_if_technology_column_exists


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # First, add any components specific to the operational modules
    for op_m in getattr(d, required_operational_modules):
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    # Then define operational constraints for all generators
    # Get rules from the generator's operational module
    def power_provision_rule(mod, g, tmp):
        """
        Power provision is a variable for some generators, but not others; get
        the appropriate expression for each generator based on its operational
        type.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            power_provision_rule(mod, g, tmp)
    m.Power_Provision_MW = Expression(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                      rule=power_provision_rule)

    # Add generation to load balance constraint
    def total_power_production_rule(mod, z, tmp):
        return sum(mod.Power_Provision_MW[g, tmp]
                   for g in mod.OPERATIONAL_PROJECTS_IN_TIMEPOINT[tmp]
                   if mod.load_zone[g] == z)
    m.Power_Production_in_Zone_MW = \
        Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                   rule=total_power_production_rule)
    getattr(d, load_balance_production_components).append(
        "Power_Production_in_Zone_MW")

    # Keep track of curtailment
    def scheduled_curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the scheduled
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            scheduled_curtailment_rule(mod, g, tmp)

    # TODO: possibly create this only if needed by another module?
    m.Scheduled_Curtailment_MW = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=scheduled_curtailment_rule
    )

    def subhourly_curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            subhourly_curtailment_rule(mod, g, tmp)

    # TODO: possibly create this only if needed by another module?
    m.Subhourly_Curtailment_MW = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=subhourly_curtailment_rule
    )

    def subhourly_energy_delivered_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            subhourly_energy_delivered_rule(mod, g, tmp)

    # TODO: possibly create this only if needed by another module?
    m.Subhourly_Energy_Delivered_MW = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=subhourly_energy_delivered_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "load_module_specific_data"):
            imported_operational_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """

    # First power
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "dispatch_all.csv"), "wb") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "power_mw"])
        for (p, tmp) in m.PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                value(m.Power_Provision_MW[p, tmp])
            ])

    # Next, export module-specific results
    # Operational type modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "export_module_specific_results"):
            imported_operational_modules[op_m].\
                export_module_specific_results(
                m, d, scenario_directory, horizon, stage,
            )
        else:
            pass

    # Reserve modules
    imported_reserve_modules = \
        load_reserve_type_modules(getattr(d, required_reserve_modules))
    for r_m in getattr(d, required_reserve_modules):
        if hasattr(imported_reserve_modules[r_m],
                   "export_module_specific_results"):
            imported_reserve_modules[r_m].export_module_specific_results(
                m, d, scenario_directory, horizon, stage
            )
        else:
            pass


def summarize_results(d, problem_directory, horizon, stage):
    """
    Summarize operational results
    :param d:
    :param problem_directory:
    :param horizon:
    :param stage:
    :return:
    """

    summary_results_file = os.path.join(
        problem_directory, horizon, stage, "results", "summary_results.txt"
    )

    # Open in 'append' mode, so that results already written by other
    # modules are not overridden
    with open(summary_results_file, "a") as outfile:
        outfile.write(
            "\n### OPERATIONAL RESULTS ###\n"
        )

    # Next, our goal is to get a summary table of power production by load
    # zone, technology, and period

    # Check if the 'technology' exists in  projects.tab; if it doesn't, we
    # don't have a category to aggregate by, so we'll skip summarizing results
    if not check_if_technology_column_exists(problem_directory):
        with open(summary_results_file, "a") as outfile:
            outfile.write(
                "...skipping aggregating operational results: column '"
                "technology' not found in projects.tab"
            )
    else:
        # Get the technology for each project by which we'll aggregate
        project_tech = \
            pd.read_csv(
                os.path.join(problem_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project", "load_zone",
                                   "technology"]
            )
        project_tech.set_index("project", inplace=True, verify_integrity=True)

        # Get the period and horizon for each timepoint
        tmp_period_horizon = \
            pd.read_csv(
                os.path.join(problem_directory, "inputs", "timepoints.tab"),
                sep="\t", usecols=["TIMEPOINTS", "period", "horizon"]
            )
        tmp_period_horizon.set_index(
            "TIMEPOINTS", inplace=True, verify_integrity=True
        )

        # Get the weight for each horizon
        horizon_weight = \
            pd.read_csv(
                os.path.join(problem_directory, "inputs", "horizons.tab"),
                sep="\t", usecols=["HORIZONS", "horizon_weight"]
            )
        horizon_weight.set_index(
            "HORIZONS", inplace=True, verify_integrity=True
        )

        # Get weight for each timepoint by joining on horizon
        tmp_period_horizon_weight = \
            pd.merge(
                left=tmp_period_horizon,
                right=horizon_weight,
                left_on="horizon",
                right_index=True,
                how="left"
            )

        # Get the results CSV as dataframe
        operational_results = \
            pd.read_csv(os.path.join(problem_directory, horizon,
                                     stage, "results", "operations.csv")
                        )

        # Set the index to 'project' for the first join
        # We'll change to this to 'timepoints' on the go during the merge
        # below for the second join
        operational_results.set_index(["project"], inplace=True)

        # Join the dataframes (i.e. add technology, load_zone and period
        # columns)
        operational_results_df = \
            pd.merge(
                left=pd.DataFrame(
                    pd.merge(left=operational_results,
                             right=project_tech,
                             how="left",
                             left_index=True,
                             right_index=True
                             )
                ).set_index("timepoint"),
                right=tmp_period_horizon_weight,
                how="left",
                left_index=True,
                right_index=True
            )

        operational_results_df["weighted_power_mwh"] = \
            operational_results_df["power_mw"] * \
            operational_results_df["horizon_weight"]

        # Aggregate total power results by load_zone, technology, and period
        operational_results_agg_df = pd.DataFrame(
            operational_results_df.groupby(by=["load_zone", "period",
                                               "technology",],
                                           as_index=True
                                           ).sum()["weighted_power_mwh"]
        )

        operational_results_agg_df.columns = ["weighted_power_mwh"]

        # Aggregate total power by load_zone and period -- we'll need this
        # to find the percentage of total power by technology (for each load
        # zone and period)
        lz_period_power_df = pd.DataFrame(
            operational_results_df.groupby(by=["load_zone", "period"],
                                           as_index=True
                                           ).sum()["weighted_power_mwh"]
        )

        # Name the power column
        operational_results_agg_df.columns = ["weighted_power_mwh"]
        # Add a column with the percentage of total power by load zone and tech
        operational_results_agg_df["percent_total_power"] = pd.Series(
            index=operational_results_agg_df.index
        )

        # Calculate the percent of total power for each tech (by load zone
        # and period)
        for indx, row in operational_results_agg_df.iterrows():
            operational_results_agg_df.percent_total_power[indx] = \
                operational_results_agg_df.weighted_power_mwh[indx] \
                / lz_period_power_df.weighted_power_mwh[indx[0], indx[1]]*100.0

        # Rename the columns for the final table
        operational_results_agg_df.columns = (["Annual Energy (MWh)",
                                               "% Total Power"])

        with open(summary_results_file, "a") as outfile:
            outfile.write("\n--> Energy Production <--\n")
            operational_results_agg_df.to_string(outfile)
            outfile.write("\n")
