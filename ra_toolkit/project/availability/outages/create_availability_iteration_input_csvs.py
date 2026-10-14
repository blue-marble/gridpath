# Copyright 2016-2025 Blue Marble Analytics LLC.
# Copyright 2026 Sylvan Energy Analytics LLC.
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
#
# simulate_unit_outages() function
# Copyright 2023 Moment Energy Insights LLC. Licensed under the Apache
# License, Version 2.0.
# Modifications Copyright 2024 Blue Marble Analytics LLC. Licensed under the
# Apache License, Version 2.0.

"""
Availability Iteration Inputs
*****************************

Run unit outage simulation and create availability iteration inputs.

===================
What this step does
===================

This module runs a Monte Carlo unit-outage simulation and writes the resulting
exogenous availability (derate) input CSVs. Using the per-unit availability
parameters loaded from ``--outage_params_input_csv`` (into the
``raw_data_unit_availability_params`` table) -- forced-outage rates
(``unit_for``), mean time to repair (``unit_mttr``), the number of units
(``n_units``), the unit weight, and the per-unit outage model
(``unit_fo_model``) -- it simulates ``--n_iterations`` independent outage
timelines for each project, drawing random forced and (under the sequential
model) repair/maintenance transitions. Units whose forced outage rate varies
with the weather are simulated once per weather iteration (see below).

The outage model is selected per unit via the ``unit_fo_model`` column and may
be one of:

    * ``Derate`` -- a static derate ``1 - unit_for`` applied in every timepoint.
    * ``MC_independent`` -- each timepoint's outage state is drawn independently
      from a uniform distribution against the forced-outage rate.
    * ``MC_sequential`` -- a sequential (exponential) failure/repair process
      driven by the forced-outage rate and ``unit_mttr`` (the implied mean time
      to failure is ``mttr * (1 / for - 1)``), preserving outage persistence
      across timepoints.
    * ``historical_year`` -- instead of simulating, a random historical year is
      sampled for the unit from ``--historical_availability_csv`` and that
      year's hourly derate series is used directly. (This is can be used for
      units whose availability is taken from a historical record rather than
      simulated; the choice is driven by the unit's ``unit_fo_model`` value,
      not by project type.)

For each project the per-unit availability adjustments are combined using each
unit's ``unit_weight`` to form a weighted project-level derate. Hybrid-storage
projects (``hybrid_stor`` set) additionally get a separately simulated derate
for the storage component. By default only rows whose derate differs from 1 are
written (as default availability in GridPath is 1); pass ``--print_ones`` to
retain all rows.

Output is written to ``--output_directory`` as one CSV per project, named
``<project>-<project_availability_scenario_id>-<project_availability_scenario_name>.csv``.
``--n_parallel_projects`` parallelizes the simulation across projects and
``--overwrite`` replaces existing files (otherwise existing files are appended
to). ``--sort`` re-sorts each output file at the end. These outage iterations
are intended to align with the weather/hydro iterations to form complete Monte
Carlo draws.

======================================
Weather-dependent forced outage rates
======================================

By default (``--weather_mode none``) every unit's forced outage rate is the
constant ``unit_for`` and the outage timelines are written at
``weather_iteration`` 0, i.e. they apply whatever the weather iteration of
the GridPath scenario iteration. A unit's forced outage rate can instead vary
by hour with the weather: set its ``unit_for_varies_by_weather`` to 1 and
provide its hourly forced outage rates by historical date (e.g. a
temperature-dependent forced outage rate curve applied to the historical
temperature series) in the ``raw_data_unit_forced_outage_rate_profiles``
table (``--forced_outage_rate_profile_input_csv`` loads them; columns
``year, month, day_of_month, hour_of_day, unit, value``). The unit's
``unit_for`` is then ignored. ``--weather_mode`` says which forced outage
rate series each weather iteration sees:

    * ``sync`` -- a weather iteration is a historical year (as in the sync
      load, profile and derate steps); the unit's series of that year is
      used. The weather iterations are the years in the profiles table.
    * ``monte_carlo`` -- a weather iteration is a synthetic year assembled
      from historical days by the ``create_monte_carlo_weather_draws`` and
      ``create_monte_carlo_weather_draw_profiles`` steps; the unit's series
      is assembled from the same days, taken from the draws of the unit's
      ``timeseries_name`` for ``--weather_bins_id`` and
      ``--weather_draws_id`` (every drawn day must have 24 hours of data).

A project with at least one such unit is simulated ``--n_iterations`` times
per weather iteration (its other units keep their constant ``unit_for``) and
its rows are keyed by ``weather_iteration`` and ``availability_iteration``;
the project's file in the ``iterations`` subdirectory of the output directory
flags it as varying by weather iteration
(``varies_by_weather_iteration``, the
``inputs_project_availability_exogenous_outage_iterations`` table in GridPath). A project with no such unit is simulated once and written at
``weather_iteration`` 0, as under ``--weather_mode none``. GridPath reads a
scenario iteration's rows at its own weather iteration for the flagged
projects and at 0 for the others. Flagging a unit under ``--weather_mode
none`` is an error rather than silently ignored.

=========================
Reproducibility (seeding)
=========================

By default seeding is OFF: ``--user_provided_seeding`` is not set, so the
outage simulation is fully random and non-reproducible from run to run. When
seeding is off, *all* of the seeding flags below are ignored -- the seed
arguments are replaced with ``None`` before the simulation runs, and NumPy's
global RNG is never explicitly seeded.

To get reproducible outages, set ``--user_provided_seeding`` together with a
``--starting_project_iteration_seed <int>`` (defaults to ``0``). With seeding
on:

    * **Per-project, non-overlapping seed ranges.** Each project is assigned a
      starting seed of ``starting_project_iteration_seed + project_idx *
      n_iterations``. Within a project the per-iteration seed starts at that
      value and is incremented by 1 for each of the ``n_iterations``
      iterations, so the seed ranges of distinct projects do not overlap.
      Under ``--weather_mode sync`` or ``monte_carlo``, the seeds of the
      projects whose outages vary by weather repeat this layout once per
      weather iteration, offset by ``weather_idx * n_projects *
      n_iterations``: the first weather iteration uses the seeds of
      ``--weather_mode none``, and each further weather iteration draws its
      own independent outages from seeds beyond every project's first block.
      A project whose outages do not vary by weather uses its first block
      only, so its timelines do not depend on the weather mode or on which
      other projects vary by weather.
    * **Per-unit seeds within an iteration.** For a given project iteration, the
      per-iteration seed is used to seed NumPy's RNG, which then draws one
      integer seed per unit via ``np.random.randint(1,
      max_integer_for_unit_outage_seeding, size=n_units_in_project)``. Each
      unit's outage timeline is then simulated from its own seed.
      ``--max_integer_for_unit_outage_seeding`` defaults to ``1000000``.
    * **Hybrid-storage offset.** For hybrid-storage projects, the storage
      component is simulated with a seed offset from the generator component's
      unit seed by ``--hybrid_storage_seed_increment`` (defaults to ``1000``).

Every project / unit / iteration still draws its own independent random outage
timeline, but the whole simulation reproduces exactly when re-run with the same
seed settings. Again, these flags are ignored unless ``--user_provided_seeding``
is set. Caution advised when seeding.

=====
Usage
=====

>>> gridpath_run_ra_toolkit --single_step create_availability_iteration_input_csvs --settings_csv PATH/TO/SETTINGS/CSV

===================
Input prerequisites
===================

This module assumes the following raw input database table has been populated:
    * raw_data_unit_availability_params

This table can be populated ahead of time, or loaded at run time by passing
``--outage_params_input_csv``. Units that use the ``historical_year`` outage
model additionally read their derate series from the CSV passed via
``--historical_availability_csv``. Units whose forced outage rate varies by
weather read ``raw_data_unit_forced_outage_rate_profiles`` (loaded at run
time by ``--forced_outage_rate_profile_input_csv``) and, under
``--weather_mode monte_carlo``, ``aux_weather_iterations``.

=========
Settings
=========
    * database
    * outage_params_input_csv
    * historical_availability_csv
    * stage_id
    * n_iterations
    * weather_mode
    * weather_bins_id
    * weather_draws_id
    * forced_outage_rate_profile_input_csv
    * study_year
    * project_availability_scenario_id
    * project_availability_scenario_name
    * output_directory
    * overwrite
    * sort
    * print_ones
    * n_parallel_projects
    * user_provided_seeding
    * starting_project_iteration_seed
    * max_integer_for_unit_outage_seeding
    * hybrid_storage_seed_increment

"""

from argparse import ArgumentParser
from gridpath.common_functions import get_version_parser
import csv
from multiprocessing import get_context
import numpy as np
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database
from db.common_functions import read_and_import_csv
from ra_toolkit.common_methods import create_csv_generic

WEATHER_MODES = ["none", "sync", "monte_carlo"]
FORCED_OUTAGE_RATE_PROFILES_TABLE = "raw_data_unit_forced_outage_rate_profiles"


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True, parents=[get_version_parser()])

    parser.add_argument("-db", "--database")
    parser.add_argument(
        "-o_csv",
        "--outage_params_input_csv",
        default=None,
        help="""Path to the unit availability  params CSV file to load into the 
        raw_data_unit_availability_params table in the database. If not 
        specified, data will be assumed to have been already loaded into the 
        database.""",
    )
    parser.add_argument(
        "-hist_csv",
        "--historical_availability_csv",
        default=None,
        help="""Path to the historical availability data CSV file to load for the
        historical_year outage model. Expected columns: year, month, day_of_month,
        hour_of_day, unit, derate. Each unit can have multiple years of hourly
        derate data. If not specified, model will not be able to use historical_year
        outage_model.""",
    )
    parser.add_argument(
        "-for_csv",
        "--forced_outage_rate_profile_input_csv",
        default=None,
        help="""Path to the hourly forced outage rate profiles CSV file to load
        into the raw_data_unit_forced_outage_rate_profiles table (columns: year,
        month, day_of_month, hour_of_day, unit, value), read for the units with
        unit_for_varies_by_weather = 1. If not specified, data will be assumed
        to have been already loaded into the database.""",
    )
    parser.add_argument("-stage", "--stage_id", default=1, help="Defaults to 1.")
    parser.add_argument(
        "-n_iter",
        "--n_iterations",
        help="The number of availability iterations to simulate (per weather "
        "iteration for the projects whose forced outage rates vary by "
        "weather).",
    )
    parser.add_argument(
        "-w_mode",
        "--weather_mode",
        default="none",
        choices=WEATHER_MODES,
        help="How the forced outage rates of the units with "
        "unit_for_varies_by_weather = 1 follow the weather iterations: 'sync' "
        "(a weather iteration is a historical year of the profiles) or "
        "'monte_carlo' (a weather iteration is a synthetic year from the "
        "weather draws). Defaults to 'none': no unit may vary by weather and "
        "the outages are written at weather_iteration 0.",
    )
    parser.add_argument(
        "-bins_id",
        "--weather_bins_id",
        default=1,
        help="The weather bins ID of the draws under --weather_mode "
        "monte_carlo. Defaults to 1.",
    )
    parser.add_argument(
        "-draws_id",
        "--weather_draws_id",
        default=1,
        help="The weather draws ID of the draws under --weather_mode "
        "monte_carlo. Defaults to 1.",
    )
    parser.add_argument(
        "-user_seeding",
        "--user_provided_seeding",
        default=False,
        action="store_true",
        help="WARNING: make sure you understand what this script does with "
        "the user-defined seeds before enabling this.",
    )
    parser.add_argument(
        "-seed",
        "--starting_project_iteration_seed",
        default=0,
        help="Starting seed for an iteration-project combination. If selected, "
        "this script increments the seed by 1 for each project-iteration. "
        "Setting the seeds will ensure that you get the same results each "
        "time, but can compromise randomness. Make sure to set "
        "'--user_provided_seeding' flag to True to use this functionality and "
        "proceed with caution. If the '--user_provided_seeding' flag is not set, "
        "this seed will be ignored.",
    )
    parser.add_argument(
        "-max_unit_seed_int",
        "--max_integer_for_unit_outage_seeding",
        default=1000000,
        type=int,
        help="The max integer for assigning seeds to each unit outage "
        "simulation for a given project. The --user_provided_seeding flag must "
        "be set to True for this to take effect. Proceed with caution.",
    )
    parser.add_argument(
        "-hyb_s_seed_inc",
        "--hybrid_storage_seed_increment",
        default=1000,
        help="The seed increment for hybrid storage components relative to "
        "the generator component. If the --user_provided_seeding flag is not set, this value will be ignored.",
    )
    parser.add_argument(
        "-s_y",
        "--study_year",
        default=0,
        help=f"Defaults to 0. Timepoint IDs will start at 1. Set to YYYY to "
        f"have timepoint IDs start at YYYY0001.",
    )
    parser.add_argument(
        "-id", "--project_availability_scenario_id", default=1, help="Defaults to 1."
    )
    parser.add_argument(
        "-name",
        "--project_availability_scenario_name",
        default="ra_toolkit",
        help="Defaults to ra_toolkit.",
    )
    parser.add_argument("-out_dir", "--output_directory")
    parser.add_argument(
        "-o",
        "--overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing files.",
    )
    parser.add_argument(
        "-sort",
        "--sort",
        default=False,
        action="store_true",
        help="Sorts output file at the " "end if enabled.",
    )

    parser.add_argument(
        "-parallel",
        "--n_parallel_projects",
        default=1,
        help="The number of projects to simulate in parallel. Defaults to 1.",
    )

    parser.add_argument(
        "-print_ones",
        "--print_ones",
        default=False,
        action="store_true",
        help="Include rows where derate values equal 1. Defaults to False.",
    )

    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_temporal_structure(study_year):
    stage_tmp_dict = {
        1: [tmp for tmp in range(study_year * 10000 + 1, study_year * 10000 + 8760 + 1)]
    }

    return stage_tmp_dict


def unit_for_varies_by_weather(row):
    """
    :param row: a raw_data_unit_availability_params row
    :return: whether the unit's forced outage rate varies by weather (a NULL
        flag means it does not)
    """
    flag = row["unit_for_varies_by_weather"]

    return pd.notna(flag) and int(flag) == 1


def get_weather_iterations(conn, weather_mode, weather_bins_id, weather_draws_id):
    """
    :return: the weather iterations to simulate the weather-varying projects
        for: the years of the forced outage rate profiles under 'sync', the
        weather iterations of the draws under 'monte_carlo', and [0] under
        'none'
    """
    if weather_mode == "none":
        return [0]
    elif weather_mode == "sync":
        weather_iterations = [
            year
            for (year,) in conn.execute(
                f"""SELECT DISTINCT year FROM {FORCED_OUTAGE_RATE_PROFILES_TABLE}
                ORDER BY year;"""
            ).fetchall()
        ]
        source = f"the {FORCED_OUTAGE_RATE_PROFILES_TABLE} table has no rows"
    else:
        weather_iterations = [
            weather_iteration
            for (weather_iteration,) in conn.execute(
                f"""SELECT DISTINCT weather_iteration FROM aux_weather_iterations
                WHERE weather_bins_id = {weather_bins_id}
                AND weather_draws_id = {weather_draws_id}
                ORDER BY weather_iteration;"""
            ).fetchall()
        ]
        source = (
            f"aux_weather_iterations has no draws for weather_bins_id "
            f"{weather_bins_id} and weather_draws_id {weather_draws_id}"
        )

    if not weather_iterations:
        raise ValueError(
            f"No weather iterations to simulate under --weather_mode "
            f"{weather_mode}: {source}."
        )

    return weather_iterations


def get_unit_for_array(
    conn,
    row,
    n_tmps,
    weather_mode,
    weather_iteration,
    weather_bins_id,
    weather_draws_id,
):
    """
    :return: (n_tmps, 1) array of the unit's hourly forced outage rate: the
        constant unit_for, or, for a unit whose forced outage rate varies by
        weather, the profile of the weather iteration's year ('sync') or of
        the weather iteration's draw days ('monte_carlo')
    """
    unit = row["unit"]
    if not unit_for_varies_by_weather(row):
        return np.full((n_tmps, 1), row["unit_for"], dtype=float)

    if weather_mode == "sync":
        values = [
            value
            for (value,) in conn.execute(
                f"""SELECT value FROM {FORCED_OUTAGE_RATE_PROFILES_TABLE}
                WHERE unit = '{unit}' AND year = {weather_iteration}
                ORDER BY month, day_of_month, hour_of_day;"""
            ).fetchall()
        ]
        if len(values) != n_tmps:
            raise ValueError(
                f"Unit {unit} has {len(values)} forced outage rate rows for "
                f"year {weather_iteration} in "
                f"{FORCED_OUTAGE_RATE_PROFILES_TABLE}; expected {n_tmps} "
                f"(one per hour of the study year)."
            )
    else:
        timeseries_name = row["timeseries_name"]
        if pd.isna(timeseries_name):
            raise ValueError(
                f"Unit {unit} needs a timeseries_name to find its draw days "
                f"in aux_weather_iterations under --weather_mode monte_carlo."
            )
        draw_days_sql = f"""
            FROM aux_weather_iterations AS d
            LEFT JOIN {FORCED_OUTAGE_RATE_PROFILES_TABLE} AS p
                ON p.year = d.{timeseries_name}_year
                AND p.month = d.{timeseries_name}_month
                AND p.day_of_month = d.{timeseries_name}_day_of_month
                AND p.unit = '{unit}'
            WHERE d.weather_bins_id = {weather_bins_id}
            AND d.weather_draws_id = {weather_draws_id}
            AND d.weather_iteration = {weather_iteration}
        """
        incomplete_days = conn.execute(f"""
            SELECT d.draw_number, d.{timeseries_name}_year,
            d.{timeseries_name}_month, d.{timeseries_name}_day_of_month,
            COUNT(p.value)
            {draw_days_sql}
            GROUP BY d.draw_number
            HAVING COUNT(p.value) != 24
            ORDER BY d.draw_number;""").fetchall()
        if incomplete_days:
            raise ValueError(
                f"Unit {unit} is missing forced outage rate rows in "
                f"{FORCED_OUTAGE_RATE_PROFILES_TABLE} for "
                f"{len(incomplete_days)} draw day(s) of weather iteration "
                f"{weather_iteration} (draw_number, year, month, "
                f"day_of_month, hours found): {incomplete_days[:10]}"
                f"{' ...' if len(incomplete_days) > 10 else ''}."
            )
        values = [value for (value,) in conn.execute(f"""SELECT p.value {draw_days_sql}
                ORDER BY d.draw_number, p.hour_of_day;""").fetchall()]
        if len(values) != n_tmps:
            raise ValueError(
                f"The draws of weather iteration {weather_iteration} give "
                f"{len(values)} hours of forced outage rates for unit {unit}; "
                f"expected {n_tmps} (one per hour of the study year)."
            )

    for_array = np.array(values, dtype=float).reshape(n_tmps, 1)
    if np.isnan(for_array).any() or (for_array < 0).any() or (for_array > 1).any():
        raise ValueError(
            f"The forced outage rates of unit {unit} for weather iteration "
            f"{weather_iteration} must be between 0 and 1 (NULLs not allowed)."
        )

    return for_array


def get_unit_for_arrays(
    conn,
    project_df,
    n_tmps,
    weather_mode,
    weather_iteration,
    weather_bins_id,
    weather_draws_id,
):
    """
    :return: {unit: (n_tmps, 1) forced outage rate array} for the project's
        units at this weather iteration
    """
    return {
        row["unit"]: get_unit_for_array(
            conn=conn,
            row=row,
            n_tmps=n_tmps,
            weather_mode=weather_mode,
            weather_iteration=weather_iteration,
            weather_bins_id=weather_bins_id,
            weather_draws_id=weather_draws_id,
        )
        for _, row in project_df.iterrows()
    }


def get_weighted_availability_adjustment(
    project_df,
    tmps,
    unit_for_arrays,
    user_provided_seeding,
    project_iteration_seed,
    max_integer_for_unit_outage_seeding,
    hyb_stor_seed_unit_increment,
    historical_data=None,
):
    project_outage_adjustment = []
    project_hyb_stor_outage_adjustment = []

    # Seed the unit seeds based on the project_iteration_seed; this will only
    # be used if --random is set to False; otherwise, the unit_seeds will be
    # reset to None
    if user_provided_seeding:
        # For each project iteration, we assign a seed to each unit outage
        # simulation based on the project_iteration_seed and a
        # max_integer_for_unit_seeding number set by the user
        # Draw a distinct generator-component seed per unit (without
        # replacement) so no two units share a seed and thus an identical
        # outage timeline. To also keep each hybrid unit's storage-component
        # seed (generator seed + hyb_stor_seed_unit_increment, assigned below)
        # from coinciding with another unit's generator or storage seed, draw
        # the generator seeds from values spaced (increment + 1) apart: no two
        # then differ by exactly the increment, so {seeds} and
        # {seeds + increment} are disjoint.
        n_units_in_project = len(project_df.index)
        seed_population = np.arange(
            1,
            max_integer_for_unit_outage_seeding,
            hyb_stor_seed_unit_increment + 1,
        )
        # Guard: np.random.choice(replace=False) cannot draw more values than
        # are available. Fail with an actionable message rather than an opaque
        # ValueError.
        if n_units_in_project > len(seed_population):
            raise ValueError(
                f"Cannot assign {n_units_in_project} distinct, "
                f"non-colliding outage seeds to project "
                f"'{project_df['project'].iloc[0]}': only "
                f"{len(seed_population)} are available given "
                f"max_integer_for_unit_outage_seeding="
                f"{max_integer_for_unit_outage_seeding} and "
                f"hybrid_storage_seed_increment={hyb_stor_seed_unit_increment}. "
                f"Increase --max_integer_for_unit_outage_seeding."
            )
        np.random.seed(project_iteration_seed)
        unit_seeds = np.random.choice(
            seed_population, size=n_units_in_project, replace=False
        )
    else:
        unit_seeds = [None for n in project_df.index]

    for index, row in project_df.iterrows():
        unit = row["unit"]
        project = row["project"]
        n_units = row["n_units"]
        unit_weight = row["unit_weight"]
        outage_model = row["unit_fo_model"]
        unit_mttr = row["unit_mttr"]
        hybrid_stor = row["hybrid_stor"]

        # This is None if no seed was provided
        unit_seed = unit_seeds[index]

        # Constant, or hourly for a unit whose forced outage rate varies by
        # weather
        unit_for_array = unit_for_arrays[unit]

        unit_outage_adjustment = simulate_unit_outages(
            outage_model=outage_model,
            for_array=unit_for_array,
            mttr=unit_mttr,
            n_units=n_units,
            unit_seed=unit_seed,
            historical_data=historical_data,
            unit=unit,
        )

        # Get the project outage
        # For hybrids, this is applied to the generator component
        project_outage_adjustment.append(unit_outage_adjustment * unit_weight)

        # For hybrids, also get the outage for the storage component
        # TODO: check that this works properly
        if hybrid_stor:
            unit_outage_adjustment = simulate_unit_outages(
                outage_model=outage_model,
                for_array=unit_for_array,
                mttr=unit_mttr,
                n_units=n_units,
                unit_seed=(
                    None
                    if unit_seed is None
                    else unit_seed + hyb_stor_seed_unit_increment
                ),
                historical_data=historical_data,
                unit=unit,
            )
            project_hyb_stor_outage_adjustment.append(
                unit_outage_adjustment * unit_weight
            )

    # Only sum the unit outages if there were units, otherwise, pass None
    if project_outage_adjustment:
        adjustment = sum(project_outage_adjustment)
    else:
        adjustment = None

    if hybrid_stor:
        hyb_stor_adjustment = sum(project_hyb_stor_outage_adjustment)
    else:
        hyb_stor_adjustment = None

    return adjustment, hyb_stor_adjustment


def simulate_project_availability(
    project_df,
    project,
    weather_iteration,
    iteration_n,
    unit_for_arrays,
    user_provided_seeding,
    project_iteration_seed,
    max_integer_for_unit_outage_seeding,
    hyb_stor_seed_unit_increment,
    stage_id,
    study_year,
    filepath,
    print_ones,
    historical_data=None,
):

    # print(f"Simulating project {project}, iteration {iteration_n}")
    stage_tmp_dict = get_temporal_structure(study_year)

    # No stage simulation at this point; assume single stage
    tmps = stage_tmp_dict[1]

    availability_derate, hyb_stor_derate = get_weighted_availability_adjustment(
        project_df=project_df,
        tmps=tmps,
        unit_for_arrays=unit_for_arrays,
        user_provided_seeding=user_provided_seeding,
        project_iteration_seed=project_iteration_seed,
        max_integer_for_unit_outage_seeding=max_integer_for_unit_outage_seeding,
        hyb_stor_seed_unit_increment=hyb_stor_seed_unit_increment,
        historical_data=historical_data,
    )

    export_df = pd.DataFrame(
        {
            "weather_iteration": [weather_iteration] * len(tmps),
            "availability_iteration": [iteration_n] * len(tmps),
            "stage_id": [stage_id] * len(tmps),
            "timepoint": tmps,
            "availability_derate_outage": availability_derate,
            "hyb_stor_cap_availability_derate": hyb_stor_derate,
        }
    )

    # Filter out rows where derate values are 1, unless print_ones is True
    if not print_ones:
        # For non-hybrids, find rows with (!=1, None)
        export_df_non_hyb = export_df[
            (
                (export_df["availability_derate_outage"] != 1)
                & (export_df["hyb_stor_cap_availability_derate"].isna())
            )
        ]

        # For hybrids, find rows where either column is not 1
        # First, skip the rows where the storage derate is NA (so that we
        # don't end up including the ones for non-hybrids)
        export_df_hyb = export_df[
            (
                (export_df["hyb_stor_cap_availability_derate"].notna())
                & (
                    (export_df["availability_derate_outage"] != 1)
                    | ((export_df["hyb_stor_cap_availability_derate"] != 1))
                )
            )
        ]

        export_df = pd.concat([export_df_non_hyb, export_df_hyb]).drop_duplicates()

    export_df.to_csv(
        filepath,
        mode="a",
        header=False,
        index=False,
    )


def simulate_unit_outages(
    outage_model,
    for_array,
    mttr,
    n_units,
    unit_seed,
    dt=1,
    starting_outage_states=None,
    historical_data=None,
    unit=None,
):
    """
    outage_model: ["Derate", "MC_independent", "MC_sequential", "historical_year"]
    FOR: numpy array with the length of the simulation window and the FOR as
        value; note this can vary by timepoint
    N_units: integer, number of units modeled
    starting_outage_states: array with the starting outage state (1/0) for
        each of the N units
    dt: outage timestep length
    historical_data: dict with unit names as keys and DataFrames containing
        historical availability data with columns: year, month, day_of_month,
        hour_of_day, unit, derate (for historical_year model)
    unit: unit name (for historical_year model)
    """
    # print(f"Simulating unit outages for {unit}... Outage model: {outage_model}")
    # Seed the simulation if requested
    if unit_seed is not None:
        np.random.seed(unit_seed)

    if starting_outage_states is None:
        starting_outage_states = []

    # TODO: probably remove derates; should be handled via default availablity
    #  values rather than writing timepoint-level derates
    if outage_model == "Derate":
        availability = 1 - np.outer(for_array, np.ones(n_units))

    elif outage_model == "MC_independent":
        # randomly draw whether each unit is out using a uniform distribution
        # LHS is an array of the simulation window length with a random number
        # the RHS is an array of the simulation window length with the forced
        # outage rate
        # the results is an array with True/False (will be True FOR percent
        # of the time), so the final result (1.0 - ()) will be an array with
        # ones and zeros in which we'll have zeros FOR percent of the time
        availability = 1.0 - (
            np.random.rand(len(for_array), n_units)
            < np.outer(for_array, np.ones(n_units))
        )

    elif outage_model == "MC_sequential":
        # initialize with starting outage states, if they are provided.
        # Otherwise, initialize with randomly selected outages
        if np.size(starting_outage_states) == 0:
            avail_last = 1.0 - (
                np.random.rand(1, n_units) < np.outer(for_array[0], np.ones(n_units))
            )
        else:
            avail_last = starting_outage_states

        # calculate mean time to failure [MTTR = FOR * (MTTR + MTTF)]; a
        # forced outage rate of 0 gives an infinite MTTF (the unit never
        # fails), so silence the division warning
        with np.errstate(divide="ignore"):
            MTTF = float(mttr) * (1 / for_array - 1)

        # Randomly draw whether each unit fails or is repaired in each time
        # step using an exponential model
        availability = np.zeros([len(for_array), n_units])

        for t in range(len(for_array)):
            # If the unit was available in the last timepoint, use the MTTF
            # to determine if it will be available in the current timepoint
            # This depends on the timepoint-dependent FOR, so MTTF is indexed
            # by timepoint
            if_avail_last = (avail_last == 1) * (
                1.0 - (np.random.exponential(MTTF[t], n_units) < dt)
            )
            if_unavail_last = (avail_last == 0) * (
                np.random.exponential(float(mttr), n_units) < dt
            )
            avail_tmp = if_avail_last + if_unavail_last
            availability[t, :] = avail_tmp
            avail_last = avail_tmp

    elif outage_model == "historical_year":
        # Sample a random year from historical data for this unit
        if historical_data is None or unit not in historical_data:
            raise ValueError(
                f"Historical data not provided for unit {unit}. "
                "Please provide historical_availability_csv."
            )

        unit_hist_data = historical_data[unit]

        # Get list of unique years in the historical data
        available_years = unit_hist_data["year"].unique()

        if len(available_years) == 0:
            raise ValueError(f"No historical years found for unit {unit}.")

        # Randomly select a year
        selected_year = np.random.choice(available_years)

        # Get the derate values for the selected year
        # Data is already sorted by year, month, day_of_month, hour_of_day
        year_data = unit_hist_data[unit_hist_data["year"] == selected_year]
        derate_values = year_data["value"].values

        # Check if we have the right number of hours
        if len(derate_values) != len(for_array):
            raise ValueError(
                f"Historical data for unit {unit}, year {selected_year} "
                f"has {len(derate_values)} hours, but expected {len(for_array)}."
            )

        # Create availability array - replicate the same derate pattern for each
        # of the n_units (this represents multiple identical units with the same
        # historical outage pattern)
        availability = np.outer(derate_values, np.ones(n_units))

    else:
        availability = np.ones([len(for_array), n_units])

    outage_adjustment = np.mean(availability, axis=1)

    return outage_adjustment


def simulate_all_project_iterations(pool_datum):
    """
    Helper function to simulate all iterations for a single project.
    This allows parallelization by project rather than by project-iteration.
    """
    [
        conn_string,
        project,
        weather_iterations,
        weather_mode,
        weather_bins_id,
        weather_draws_id,
        n_iterations,
        weather_iteration_seed_stride,
        user_provided_seeding,
        starting_project_iteration_seed,
        max_integer_for_unit_outage_seeding,
        hyb_stor_seed_unit_increment,
        stage_id,
        study_year,
        filepath,
        print_ones,
        historical_data,
    ] = pool_datum

    # Reconnect to database in this process
    conn = connect_to_database(conn_string)
    try:
        simulate_all_project_iterations_with_conn(
            conn=conn,
            project=project,
            weather_iterations=weather_iterations,
            weather_mode=weather_mode,
            weather_bins_id=weather_bins_id,
            weather_draws_id=weather_draws_id,
            n_iterations=n_iterations,
            weather_iteration_seed_stride=weather_iteration_seed_stride,
            user_provided_seeding=user_provided_seeding,
            starting_project_iteration_seed=starting_project_iteration_seed,
            max_integer_for_unit_outage_seeding=max_integer_for_unit_outage_seeding,
            hyb_stor_seed_unit_increment=hyb_stor_seed_unit_increment,
            stage_id=stage_id,
            study_year=study_year,
            filepath=filepath,
            print_ones=print_ones,
            historical_data=historical_data,
        )
    finally:
        conn.close()


def simulate_all_project_iterations_with_conn(
    conn,
    project,
    weather_iterations,
    weather_mode,
    weather_bins_id,
    weather_draws_id,
    n_iterations,
    weather_iteration_seed_stride,
    user_provided_seeding,
    starting_project_iteration_seed,
    max_integer_for_unit_outage_seeding,
    hyb_stor_seed_unit_increment,
    stage_id,
    study_year,
    filepath,
    print_ones,
    historical_data,
):
    # ORDER BY unit so each unit maps to the same drawn seed (unit_seeds is
    # indexed positionally) across runs; required for reproducible draws
    project_df = pd.read_sql(
        f"""
            SELECT * FROM raw_data_unit_availability_params
            WHERE project = '{project}'
            ORDER BY unit
            ;""",
        conn,
    )
    n_tmps = len(get_temporal_structure(study_year)[1])

    # Loop through all weather iterations (a single 0 for a project whose
    # outages do not vary by weather) and all availability iterations for
    # this project; the seed increments by 1 per availability iteration and
    # each weather iteration's block of seeds is offset by the stride (all
    # projects' first blocks), so the first weather iteration draws what
    # --weather_mode none would
    for weather_idx, weather_iteration in enumerate(weather_iterations):
        project_iteration_seed = (
            starting_project_iteration_seed
            + weather_idx * weather_iteration_seed_stride
        )
        unit_for_arrays = get_unit_for_arrays(
            conn=conn,
            project_df=project_df,
            n_tmps=n_tmps,
            weather_mode=weather_mode,
            weather_iteration=weather_iteration,
            weather_bins_id=weather_bins_id,
            weather_draws_id=weather_draws_id,
        )
        for iteration_n in range(1, n_iterations + 1):
            simulate_project_availability(
                project_df=project_df,
                project=project,
                weather_iteration=weather_iteration,
                iteration_n=iteration_n,
                unit_for_arrays=unit_for_arrays,
                user_provided_seeding=user_provided_seeding,
                project_iteration_seed=(
                    project_iteration_seed if user_provided_seeding else None
                ),
                max_integer_for_unit_outage_seeding=(
                    max_integer_for_unit_outage_seeding
                    if user_provided_seeding
                    else None
                ),
                hyb_stor_seed_unit_increment=(
                    hyb_stor_seed_unit_increment if user_provided_seeding else None
                ),
                stage_id=stage_id,
                study_year=study_year,
                filepath=filepath,
                print_ones=print_ones,
                historical_data=historical_data,
            )

            project_iteration_seed += 1


def sort_csv_file(filepath, columns_to_sort_by, ascending):
    df = pd.read_csv(filepath, delimiter=",", low_memory=False, on_bad_lines="warn")
    df.sort_values(by=columns_to_sort_by, ascending=ascending, inplace=True)

    df.to_csv(
        filepath,
        mode="w",
        header=True,
        index=False,
    )


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    if not parsed_args.quiet:
        print("Creating availability iteration CSVs...")

    conn = connect_to_database(parsed_args.database)
    try:

        # ### Load data from CSV
        if parsed_args.outage_params_input_csv is not None:
            read_and_import_csv(
                conn=conn,
                f_path=parsed_args.outage_params_input_csv,
                table="raw_data_unit_availability_params",
            )

        if parsed_args.forced_outage_rate_profile_input_csv is not None:
            read_and_import_csv(
                conn=conn,
                f_path=parsed_args.forced_outage_rate_profile_input_csv,
                table=FORCED_OUTAGE_RATE_PROFILES_TABLE,
            )

        # Load historical availability data if provided
        # Not loaded into the database for now
        historical_data = None
        if parsed_args.historical_availability_csv is not None:
            # Read the CSV file directly into a DataFrame
            hist_df = pd.read_csv(parsed_args.historical_availability_csv)

            # Expected columns: year, month, day_of_month, hour_of_day, unit, derate
            # Create an hour index for ordering (1-8760 or 1-8784 for leap years)
            # Sort by temporal columns to ensure proper ordering
            hist_df = hist_df.sort_values(
                ["year", "month", "day_of_month", "hour_of_day"]
            )

            # Group by unit for unit-level access
            historical_data = {unit: group for unit, group in hist_df.groupby("unit")}

        # Make out directory if it doesn't exist
        if not os.path.exists(parsed_args.output_directory):
            os.makedirs(parsed_args.output_directory)

        # Get projects and whether their forced outage rates vary by weather
        # (any unit's does). ORDER BY so that project_idx (and therefore each
        # project's seed base, starting_project_iteration_seed + project_idx *
        # iterations_per_project) is stable across runs -- otherwise seeded
        # results are not reproducible.
        projects = conn.execute("""
            SELECT project, MAX(COALESCE(unit_for_varies_by_weather, 0))
            FROM raw_data_unit_availability_params
            GROUP BY project
            ORDER BY project;
            """).fetchall()
        weather_varying_projects = [prj for prj, varies in projects if varies]

        weather_mode = parsed_args.weather_mode
        if weather_mode == "none" and weather_varying_projects:
            raise ValueError(
                f"The forced outage rates of projects {weather_varying_projects} "
                f"vary by weather (unit_for_varies_by_weather = 1) but "
                f"--weather_mode is 'none'; set it to 'sync' or 'monte_carlo' or "
                f"unflag the units."
            )
        weather_iterations = get_weather_iterations(
            conn=conn,
            weather_mode=weather_mode,
            weather_bins_id=parsed_args.weather_bins_id,
            weather_draws_id=parsed_args.weather_draws_id,
        )
        if not parsed_args.quiet and weather_mode != "none":
            print(
                f"   ...forced outage rates of projects {weather_varying_projects} "
                f"vary by weather; simulating them for weather iterations "
                f"{weather_iterations} ({weather_mode})"
            )

        all_files = []
        pool_data = []
        project_iteration_seed = int(parsed_args.starting_project_iteration_seed)
        hyb_stor_seed_unit_increment = int(parsed_args.hybrid_storage_seed_increment)
        n_iterations = int(parsed_args.n_iterations)

        # Calculate total iterations per project for seed incrementing; the
        # weather iterations of the weather-varying projects repeat the layout
        # of all projects' seed ranges with this stride
        iterations_per_project = n_iterations
        weather_iteration_seed_stride = len(projects) * n_iterations

        for project_idx, (project, varies_by_weather) in enumerate(projects):
            # Write header if we are overwriting the file or it doesn't exist
            overwrite = parsed_args.overwrite
            header = [
                "weather_iteration",
                "availability_iteration",
                "stage_id",
                "timepoint",
                "availability_derate_outage",
                "hyb_stor_cap_availability_derate_outage",
            ]

            filepath = os.path.join(
                parsed_args.output_directory,
                f"{project}-{parsed_args.project_availability_scenario_id}-{parsed_args.project_availability_scenario_name}.csv",
            )
            all_files.append(filepath)

            if not os.path.exists(filepath) or overwrite:
                with open(filepath, "w", newline="") as f:
                    csvwriter = csv.writer(f, lineterminator="\n")
                    csvwriter.writerow(header)

            # Calculate starting seed for this project
            starting_seed_for_project = (
                int(parsed_args.starting_project_iteration_seed)
                + project_idx * iterations_per_project
            )

            # Create pool data entry for this project (all iterations)
            pool_data.append(
                [
                    parsed_args.database,
                    project,
                    weather_iterations if varies_by_weather else [0],
                    weather_mode,
                    parsed_args.weather_bins_id,
                    parsed_args.weather_draws_id,
                    n_iterations,
                    weather_iteration_seed_stride,
                    parsed_args.user_provided_seeding,
                    starting_seed_for_project,
                    parsed_args.max_integer_for_unit_outage_seeding,
                    hyb_stor_seed_unit_increment,
                    parsed_args.stage_id,
                    int(parsed_args.study_year),
                    filepath,
                    parsed_args.print_ones,
                    historical_data,
                ]
            )

        pool_data = tuple(pool_data)

        # Pool must use spawn to work properly on Linux; the context manager
        # terminates the pool if a worker raises
        with get_context("spawn").Pool(int(parsed_args.n_parallel_projects)) as pool:
            pool.map(simulate_all_project_iterations, pool_data)

        # Flag the projects whose outages vary by weather iteration (GridPath
        # reads the others at weather_iteration 0)
        iterations_directory = os.path.join(parsed_args.output_directory, "iterations")
        os.makedirs(iterations_directory, exist_ok=True)
        for project, varies_by_weather in projects:
            create_csv_generic(
                filename=os.path.join(
                    iterations_directory,
                    f"{project}-{parsed_args.project_availability_scenario_id}-"
                    f"{parsed_args.project_availability_scenario_name}.csv",
                ),
                df=pd.DataFrame(
                    {"varies_by_weather_iteration": [int(bool(varies_by_weather))]}
                ),
                overwrite=True,
            )

        # Sort the resulting CSV file if requested
        # TODO: could parallelize this
        if parsed_args.sort:
            for filepath in all_files:
                sort_csv_file(
                    filepath=filepath,
                    columns_to_sort_by=[
                        "weather_iteration",
                        "availability_iteration",
                        "stage_id",
                        "timepoint",
                    ],
                    ascending=[True, True, True, True],
                )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
