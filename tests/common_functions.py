from pyomo.environ import AbstractModel, DataPortal


def add_model_components(prereq_modules, module_to_test):
    """
    Create abstract model, add components from prerequisite modules, add
    components from the module being tested
    :param prereq_modules:
    :param module_to_test:
    :return:
    """
    m = AbstractModel()
    for mod in prereq_modules:
        if hasattr(mod, 'add_model_components'):
            mod.add_model_components(m, None)
    module_to_test.add_model_components(m, None)

    return m


def add_components_and_load_data(prereq_modules, module_to_test, test_data_dir):
    """
    Test that data are loaded with no errors
    :return:
    """
    m = add_model_components(prereq_modules, module_to_test)
    data = DataPortal()
    for mod in prereq_modules:
        if hasattr(mod, 'load_model_data'):
            mod.load_model_data(m, None, data, test_data_dir, "", "")
    module_to_test.load_model_data(m, None, data, test_data_dir, "", "")

    return m, data
