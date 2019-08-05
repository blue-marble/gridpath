# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.api.common_functions import connect_to_database


# ### API: Scenario Detail ### #
class ScenarioDetailName(Resource):
    """
    The name of the a scenario by scenario ID
    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='scenario_name'
        )[0]["value"]

        return scenario_detail_api


class ScenarioDetailAll(Resource):
    """
    All settings for a scenario ID.
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='*'
        )

        scenario_edit_api = {}
        for column in scenario_detail_api:
            scenario_edit_api[column['name']] = column['value']

        return scenario_edit_api


class ScenarioDetailFeatures(Resource):
    """
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string=
            'feature_fuels, feature_transmission, '
            'feature_transmission_hurdle_rates,'
            'feature_simultaneous_flow_limits, feature_load_following_up, '
            'feature_load_following_down, feature_regulation_up, '
            'feature_regulation_down, feature_spinning_reserves, '
            'feature_frequency_response, '
            'feature_rps, feature_carbon_cap, feature_track_carbon_imports, '
            'feature_prm, feature_elcc_surface, feature_local_capacity'
        )

        return scenario_detail_api


class ScenarioDetailTemporal(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='temporal'
        )

        return scenario_detail_api


class ScenarioDetailGeographyLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_load_zones, project_load_zones, '
                               'transmission_load_zones'
            )
        else:
            scenario_detail_api = get_scenario_detail(
              db_path=self.db_path,
              scenario_id=scenario_id,
              columns_string='geography_load_zones, project_load_zones, '
                             '"WARNING: transmission feature disabled" AS '
                             'transmission_load_zones'
            )

        return scenario_detail_api


class ScenarioDetailLoad(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='load_profile'
        )

        return scenario_detail_api


class ScenarioDetailProjectCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='project_portfolio, project_existing_capacity, '
                           'project_existing_fixed_cost, project_new_cost, '
                           'project_new_potential, project_availability'
        )

        return scenario_detail_api


class ScenarioDetailProjectOpChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            columns_string='project_operating_chars'
        )

        return scenario_detail_api


class ScenarioDetailFuels(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_fuels'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='project_fuels, fuel_prices'
            )
        else:
            scenario_detail_api = [
                {"name": "project_fuels",
                 "value": "WARNING: fuels feature disabled"},
                {"name": "fuel_prices",
                 "value": "WARNING: fuels feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailTransmissionCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='transmission_portfolio, '
                               'transmission_existing_capacity '
            )
        else:
            scenario_detail_api = [
                {"name": "transmission_portfolio",
                 "value": "WARNING: transmission feature disabled"},
                {"name": "transmission_existing_capacity",
                 "value": "WARNING: transmission feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailTransmissionOpChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='transmission_operational_chars'
            )
        else:
            scenario_detail_api = [
                {"name": "transmission_operational_chars",
                 "value": "WARNING: transmission feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailTransmissionHurdleRates(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string=
                                  'of_transmission_hurdle_rates'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='transmission_hurdle_rates'
            )
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_transmission') \
                and not check_feature(db_path=self.db_path,
                                      scenario_id=scenario_id,
                                      column_string=
                                      'of_transmission_hurdle_rates'):
            scenario_detail_api = [
                {"name": "transmission_hurdle_rates",
                 "value": "WARNING: both transmission and transmission "
                          "hurdle rates features disabled"}
            ]
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_transmission') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string=
                                  'of_transmission_hurdle_rates'):
            scenario_detail_api = [
                {"name": "transmission_hurdle_rates",
                 "value": "WARNING: transmission feature disabled"}
            ]
        else:
            scenario_detail_api = [
                {"name": "transmission_hurdle_rates",
                 "value": "WARNING: transmission hurdle rates feature "
                          "disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailTransmissionSimFlow(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_transmission') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string='of_simultaneous_flow_limits'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string=
                'transmission_simultaneous_flow_limits, '
                'transmission_simultaneous_flow_limit_line_groups'
            )
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_transmission') \
                and not check_feature(db_path=self.db_path,
                                      scenario_id=scenario_id,
                                      column_string=
                                      'of_simultaneous_flow_limits'):
            scenario_detail_api = [
                {"name": "transmission_simultaneous_flow_limits",
                 "value": "WARNING: both transmission and simultaneous flow "
                          "limits features disabled"},
                {"name": "transmission_simultaneous_flow_limit_line_groups",
                 "value": "WARNING: both transmission and simultaneous flow "
                          "limits features disabled"}
            ]
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_transmission') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string='of_simultaneous_flow_limits'):
            scenario_detail_api = [
                {"name": "transmission_simultaneous_flow_limits",
                 "value": "WARNING: transmission feature disabled"},
                {"name": "transmission_simultaneous_flow_limit_line_groups",
                 "value": "WARNING: transmission feature disabled"}
            ]
        else:
            scenario_detail_api = [
                {"name": "transmission_simultaneous_flow_limits",
                 "value": "WARNING: simultaneous flow limits feature "
                          "disabled"},
                {"name": "transmission_simultaneous_flow_limit_line_groups",
                 "value": "WARNING: simultaneous flow limits feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailLoadFollowingUp(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_lf_reserves_up'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_lf_up_bas, '
                               'load_following_reserves_up_profile, '
                               'project_lf_up_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "load_following_reserves_up_profile",
                 "value": "WARNING: load-following reserves up feature "
                          "disabled"},
                {"name": "project_lf_up_bas",
                 "value": "WARNING: load-following reserves up feature "
                          "disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailLoadFollowingDown(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_lf_reserves_down'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_lf_down_bas, '
                               'load_following_reserves_down_profile, '
                               'project_lf_down_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "load_following_reserves_down_profile",
                 "value": "WARNING: load-following reserves down feature "
                          "disabled"},
                {"name": "project_lf_down_bas",
                 "value": "WARNING: load-following reserves down feature "
                          "disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailRegulationUp(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_regulation_up'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_reg_up_bas, '
                               'regulation_up_profile, '
                               'project_reg_up_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "regulation_up_profile",
                 "value": "WARNING: regulation up feature disabled"},
                {"name": "project_reg_up_bas",
                 "value": "WARNING: regulation up feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailRegulationDown(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_regulation_down'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_reg_down_bas, '
                               'regulation_down_profile, '
                               'project_reg_down_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "regulation_down_profile",
                 "value": "WARNING: regulation down feature disabled"},
                {"name": "project_reg_down_bas",
                 "value": "WARNING: regulation down feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailSpinningReserves(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_spinning_reserves'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_spin_bas, '
                               'spinning_reserves_profile, '
                               'project_spin_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "spinning_reserves_profile",
                 "value": "WARNING: spinning reserves feature disabled"},
                {"name": "project_spin_bas",
                 "value": "WARNING: spinning reserves feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailFrequencyResponse(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_frequency_response'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='geography_freq_resp_bas, '
                               'frequency_response_profile, '
                               'project_freq_resp_bas'
            )
        else:
            scenario_detail_api = [
                {"name": "frequency_response_profile",
                 "value": "WARNING: frequency response feature disabled"},
                {"name": "project_freq_resp_bas",
                 "value": "WARNING: frequency response feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailRPS(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_rps'):
            scenario_detail_api = get_scenario_detail(
              db_path=self.db_path,
              scenario_id=scenario_id,
              columns_string='geography_rps_areas, '
                             'rps_target, '
                             'project_rps_areas'
            )
        else:
            scenario_detail_api = [
                {"name": "rps_target",
                 "value": "WARNING: RPS feature disabled"},
                {"name": "project_rps_areas",
                 "value": "WARNING: RPS feature disabled"}
            ]

        return scenario_detail_api


class ScenarioDetailCarbonCap(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_carbon_cap') \
                and check_feature(db_path=self.db_path,
                                  scenario_id=scenario_id,
                                  column_string='of_track_carbon_imports'):
            scenario_detail_api = get_scenario_detail(
              db_path=self.db_path,
              scenario_id=scenario_id,
              columns_string='carbon_cap_areas, '
                             'carbon_cap, '
                             'project_carbon_cap_areas, '
                             'transmission_carbon_cap_zones'
            )
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_carbon_cap'):
            scenario_detail_api = [
                {"name": "carbon_cap_areas",
                 "value": "WARNING: carbon cap feature disabled"},
                {"name": "carbon_cap",
                 "value": "WARNING: carbon cap feature disabled"},
                {"name": "projefct_carbon_cap_areas",
                 "value": "WARNING: carbon cap feature disabled"},
                {"name": "transmission_carbon_cap_zone_scenario_id",
                 "value": "WARNING: carbon cap feature disabled"}
            ]
        else:
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='carbon_cap_areas, '
                               'carbon_cap, '
                               'project_carbon_cap_areas, '
                               '"WARNING: tracking carbon imports feature '
                               'disabled" AS'
                               'transmission_carbon_cap_zone_scenario_id'
            )

        return scenario_detail_api


class ScenarioDetailPRM(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_prm'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='prm_areas, '
                               'prm_requirement, '
                               'project_prm_areas, '
                               'project_elcc_chars, '
                               'elcc_surface, '
                               'project_prm_energy_only'
            )
        elif not check_feature(db_path=self.db_path,
                               scenario_id=scenario_id,
                               column_string='of_prm'):
            scenario_detail_api = [
                {"name": "prm_areas",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "prm_requirement",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "project_prm_areas",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "elcc_surface",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "project_elcc_chars",
                 "value": "WARNING: PRM feature disabled"},
                {"name": "project_prm_energy_only",
                 "value": "WARNING: PRM feature disabled"}
            ]
        else:
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='prm_areas, '
                               'prm_requirement, '
                               'project_prm_areas, '
                               '"WARNING: ELCC surface feature disabled" '
                               'AS elcc_surface, '
                               'project_prm_areas, '
                               '"WARNING: ELCC surface feature disabled" '
                               'AS project_elcc_chars, '
                               'project_prm_energy_only'
            )

        return scenario_detail_api


class ScenarioDetailLocalCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        if check_feature(db_path=self.db_path,
                         scenario_id=scenario_id,
                         column_string='of_local_capacity'):
            scenario_detail_api = get_scenario_detail(
                db_path=self.db_path,
                scenario_id=scenario_id,
                columns_string='local_capacity_areas, '
                               'local_capacity_requirement, '
                               'project_local_capacity_areas, '
                               'project_local_capacity_chars'
            )
        else:
            scenario_detail_api = [
                {"name": "local_capacity_areas",
                 "value": "WARNING: local capacity feature disabled"},
                {"name": "local_capacity_requirement",
                 "value": "WARNING: local capacity feature disabled"},
                {"name": "project_local_capacity_areas",
                 "value": "WARNING: local capacity feature disabled"},
                {"name": "project_local_capacity_chars",
                 "value": "WARNING: local capacity feature disabled"}
            ]

        return scenario_detail_api


def get_scenario_detail(db_path, scenario_id, columns_string):
    """
    :param db_path: the path to the database
    :param scenario_id: integer, the scenario ID
    :param columns_string: string defining which columns to select
    :return:


    """
    io, c = connect_to_database(db_path=db_path)

    scenario_detail_query = c.execute(
        """SELECT {}
        FROM scenarios_view
        WHERE scenario_id = {};""".format(columns_string, scenario_id)
    )

    column_names = [s[0] for s in scenario_detail_query.description]
    column_values = list(list(scenario_detail_query)[0])
    scenario_detail_dict = dict(zip(column_names, column_values))

    scenario_detail_api = []
    for key in scenario_detail_dict.keys():
        scenario_detail_api.append(
            {'name': key, 'value': scenario_detail_dict[key]}
        )

    return scenario_detail_api


def check_feature(db_path, scenario_id, column_string):
    """
    :param db_path: path to to the database file
    :param scenario_id: integer, the scenario_id value in the database
    :param column_string: the columns to check
    :return: 1 or 0, depending on whether the feature is selected
    """
    io, c = connect_to_database(db_path=db_path)

    scenario_feature_on = c.execute(
        """SELECT {}
        FROM scenarios
        WHERE scenario_id = {};""".format(column_string, scenario_id)
    ).fetchone()[0]

    return scenario_feature_on
