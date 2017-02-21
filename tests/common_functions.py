from pyomo.environ import AbstractModel, DataPortal
from gridpath.auxiliary.dynamic_components import DynamicComponents


def determine_dynamic_components(prereq_modules, module_to_test, test_data_dir,
                                 horizon, stage):
    """

    :param prereq_modules:
    :param module_to_test:
    :param dynamic_inputs:
    :param horizon:
    :param stage:
    :return:
    """
    d = DynamicComponents()

    for mod in prereq_modules:
        if hasattr(mod, 'determine_dynamic_components'):
            mod.determine_dynamic_components(d, test_data_dir, "", "")
    if hasattr(module_to_test, "determine_dynamic_components"):
        module_to_test.determine_dynamic_components(
            d, test_data_dir, horizon, stage)

    return d


def add_model_components(prereq_modules, module_to_test, model, dynamic_inputs):
    """
    Create abstract model, add components from prerequisite modules, add
    components from the module being tested
    :param prereq_modules:
    :param module_to_test:
    :param model:
    :param dynamic_inputs:
    :return:
    """
    for m in prereq_modules:
        if hasattr(m, 'add_model_components'):
            m.add_model_components(model, dynamic_inputs)
    if hasattr(module_to_test, "add_model_components"):
        module_to_test.add_model_components(model, dynamic_inputs)
    if hasattr(module_to_test, "add_module_specific_components"):
        module_to_test.add_module_specific_components(model, dynamic_inputs)

    return model


def create_abstract_model(prereq_modules, module_to_test, test_data_dir,
                          horizon, stage):
    """
    Determine dynamic components and build abstract model
    :param prereq_modules:
    :param module_to_test:
    :param test_data_dir:
    :param horizon:
    :param stage:
    :return:
    """
    d = determine_dynamic_components(prereq_modules, module_to_test,
                                     test_data_dir, horizon, stage)
    m = AbstractModel()
    add_model_components(prereq_modules, module_to_test, m, d)

    return m, d


def add_components_and_load_data(prereq_modules, module_to_test, test_data_dir,
                                 horizon, stage):
    """
    Test that data are loaded with no errors
    :return:
    """

    m, d = create_abstract_model(prereq_modules, module_to_test, test_data_dir,
                                 horizon, stage)
    data = DataPortal()
    for mod in prereq_modules:
        if hasattr(mod, 'load_model_data'):
            mod.load_model_data(m, d, data, test_data_dir, horizon, stage)
    if hasattr(module_to_test, "load_model_data"):
        module_to_test.load_model_data(m, d, data, test_data_dir,
                                       horizon, stage)
    if hasattr(module_to_test, "load_module_specific_data"):
        module_to_test.load_module_specific_data(m, data, test_data_dir,
                                                  horizon, stage)

    return m, data
