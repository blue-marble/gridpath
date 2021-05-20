"""

"""

import csv
import os.path
from pyomo.environ import Param, Set

from gridpath.auxiliary.auxiliary import cursor_to_df, \
    subset_init_by_param_value
from gridpath.auxiliary.db_interface import update_prj_zone_column, \
    determine_table_subset_by_start_and_column
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_idxs


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`CARBON_TAX_PRJS`                                                     |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | Two set of carbonaceous projects we need to track for the carbon tax.   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`carbon_tax_zone`                                               |
    | | *Defined over*: :code:`CARBON_TAX_PRJS`                                     |
    | | *Within*: :code:`CARBON_TAX_ZONES`                                    |
    |                                                                         |
    | This param describes the carbon tax zone for each carbonaceous project. |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`CARBON_TAX_PRJS_BY_CARBON_TAX_ZONE`                                  |
    | | *Defined over*: :code:`CARBON_TAX_ZONES`                              |
    | | *Within*: :code:`CARBON_TAX_PRJS`                                           |
    |                                                                         |
    | Indexed set that describes the list of carbonaceous projects for each   |
    | carbon tax zone.                                                        |
    +-------------------------------------------------------------------------+
    | | :code:`CARBON_TAX_PRJ_OPR_TMPS`                                             |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | Two-dimensional set that defines all project-timepoint combinations     |
    | when a carbonaceous project can be operational.                         |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.CARBON_TAX_PRJS = Set(
        within=m.PROJECTS
    )

    # Input Params
    ###########################################################################

    m.carbon_tax_zone = Param(
        m.CARBON_TAX_PRJS,
        within=m.CARBON_TAX_ZONES
    )

    # Derived Sets
    ###########################################################################

    m.CARBON_TAX_PRJS_BY_CARBON_TAX_ZONE = Set(
        m.CARBON_TAX_ZONES,
        within=m.CARBON_TAX_PRJS,
        initialize=lambda mod, co2_z: subset_init_by_param_value(
            mod, "CARBON_TAX_PRJS", "carbon_tax_zone", co2_z
        )
    )

    m.CARBON_TAX_PRJ_OPR_TMPS = Set(
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod:
        [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
         if p in mod.CARBON_TAX_PRJS]
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                              "inputs", "projects.tab"),
        select=("project", "carbon_tax_zone"),
        param=(m.carbon_tax_zone,)
    )

    data_portal.data()['CARBON_TAX_PRJS'] = {
        None: list(data_portal.data()['carbon_tax_zone'].keys())
    }


# Database
###############################################################################

def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    project_zones = c.execute(
        """SELECT project, carbon_tax_zone
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
        ) as prj_tbl
        LEFT OUTER JOIN 
        -- Get carbon tax zones for those projects
        (SELECT project, carbon_tax_zone
            FROM inputs_project_carbon_tax_zones
            WHERE project_carbon_tax_zone_scenario_id = {}
        ) as prj_ct_zone_tbl
        USING (project)
        -- Filter out projects whose carbon tax zone is not one included in 
        -- our carbon_tax_zone_scenario_id
        WHERE carbon_tax_zone in (
                SELECT carbon_tax_zone
                    FROM inputs_geography_carbon_tax_zones
                    WHERE carbon_tax_zone_scenario_id = {}
        );
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_CARBON_TAX_ZONE_SCENARIO_ID,
            subscenarios.CARBON_TAX_ZONE_SCENARIO_ID
        )
    )

    return project_zones


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage,
                       conn):
    """
    Get inputs from database and write out the model input
    projects.tab file (to be precise, amend it).
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    project_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_zone_dict = dict()
    for (prj, zone) in project_zones:
        prj_zone_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t",
                            lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("carbon_tax_zone")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_zone_dict.keys()):
                row.append(prj_zone_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"), "w",
              newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t",
                            lineterminator="\n")
        writer.writerows(new_rows)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("update carbon tax zones")

    tables_to_update = determine_table_subset_by_start_and_column(
        conn=db, tbl_start="results_project_", cols=["carbon_tax_zone"]
    )

    for tbl in tables_to_update:
        update_prj_zone_column(
            conn=db, scenario_id=scenario_id, subscenarios=subscenarios,
            subscenario="project_carbon_tax_zone_scenario_id",
            subsc_tbl="inputs_project_carbon_tax_zones",
            prj_tbl=tbl, col="carbon_tax_zone"
        )


# Validation
###############################################################################

def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    project_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    # Convert input data into pandas DataFrame
    df = cursor_to_df(project_zones)
    zones_w_project = df["carbon_tax_zone"].unique()

    # Get the required carbon tax zones
    # TODO: make this into a function similar to get_projects()?
    #  could eventually centralize all these db query functions in one place
    c = conn.cursor()
    zones = c.execute(
        """SELECT carbon_tax_zone FROM inputs_geography_carbon_tax_zones
        WHERE carbon_tax_zone_scenario_id = {}
        """.format(subscenarios.CARBON_TAX_ZONE_SCENARIO_ID)
    )
    zones = [z[0] for z in zones]  # convert to list

    # Check that each carbon tax zone has at least one project assigned to it
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_carbon_tax_zones",
        severity="High",
        errors=validate_idxs(actual_idxs=zones_w_project,
                             req_idxs=zones,
                             idx_label="carbon_tax_zone",
                             msg="Each carbon tax zone needs at least 1 "
                                 "project assigned to it.")
    )

    # TODO: need validation that projects with carbon tax zones also have fuels