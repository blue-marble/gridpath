from setuptools import find_packages, setup

# Get version
version = {}
with open("./version.py") as fp:
    exec(fp.read(), version)

# Set up extras
extras_doc = [
    "Sphinx==7.2.6",
    "sphinx-argparse==0.4.0",
    "df2img",
]

extras_black = ["black"]

extras_coverage = [
    "coverage",  # test coverage
    "coveralls",  # automated coverage results
]

extras_gurobi = ["gurobipy"]  # Gurobi Python interface
extras_highs = ["highspy"]  # HiGHS Python interface

extras_all = extras_doc + extras_black + extras_coverage + extras_gurobi + extras_highs

setup(
    name="GridPath",
    version=version["__version__"],
    description="A versatile simulation and optimization platform for "
    "power-system planning and operations.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://www.gridpath.io",
    project_urls={
        "Discussions": "https://github.com/blue-marble/gridpath/discussions",
        "Documentation": "https://gridpath.readthedocs.io/en/latest/",
        "Issues": "https://github.com/blue-marble/gridpath/issues",
        "Source Code": "https://github.com/blue-marble/gridpath",
    },
    maintainer="Blue Marble Analytics LLC",
    maintainer_email="info@gridpath.io",
    license="Apache v2",
    platforms=["MacOS", "Windows", "Linux"],
    keywords=["energy", "electricity", "power", "renewables", "planning", "operations"],
    packages=find_packages(),
    install_requires=[
        "Pyomo==6.9.4",  # Optimization modeling language
        "pandas==2.3.2",  # Data-processing
        "bokeh==3.8.0",  # Visualization library
        "pscript==0.8.0",  # Python to JavaScript compiler (for viz)
        "networkx==3.4.2; python_version < '3.11'",  # network package for DC OPF
        "networkx==3.5.0; python_version >= '3.11'",  # network package for DC OPF
        "PyUtilib==6.0.0",  # used for solver temp file management
        "dill==0.3.8",  # pickling
        "duckdb==1.4.0",  # data-handling
    ],
    extras_require={
        "doc": extras_doc,
        "all": extras_all,
        "coverage": extras_coverage,
        "gurobi": extras_gurobi,
        "highs": extras_highs,
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "gridpath_run = gridpath.run_scenario:main",
            "gridpath_run_parallel = gridpath.run_scenario_parallel:main",
            "gridpath_run_e2e = gridpath.run_end_to_end:main",
            "gridpath_get_inputs = gridpath.get_scenario_inputs:main",
            "gridpath_import_results = " "gridpath.import_scenario_results:main",
            "gridpath_process_results = gridpath.process_results:main",
            "gridpath_validate = gridpath.validate_inputs:main",
            "gridpath_run_server = ui.server.run_server:main",
            "gridpath_run_queue_manager = ui.server.run_queue_manager:main",
            "gridpath_create_database = db.create_database:main",
            "gridpath_load_csvs = db.utilities.port_csvs_to_db:main",
            "gridpath_load_scenarios = db.utilities.scenario:main",
            "gridpath_get_pudl_data = "
            "data_toolkit.raw_data.pudl.download_data_from_pudl:main",
            "gridpath_pudl_to_gridpath_raw = "
            "data_toolkit.raw_data.pudl.pudl_to_gridpath_raw_data:main",
            "gridpath_get_pcm_demo_inputs = "
            "data_toolkit.raw_data.get_pcm_demo_user_defined_inputs:main",
            "gridpath_get_ra_toolkit_data_raw = "
            "data_toolkit.raw_data.ra_toolkit.get_ra_toolkit_data:main",
            "gridpath_run_data_toolkit = data_toolkit.run_data_toolkit:main",
            "gridpath_viz_capacity_factor_plot = viz.capacity_factor_plot:main",
            "gridpath_viz_capacity_new_plot = viz.capacity_new_plot:main",
            "gridpath_viz_capacity_retired_plot = viz.capacity_retired_plot:main",
            "gridpath_viz_capacity_total_loadzone_comparison_plot = viz.capacity_total_loadzone_comparison_plot:main",
            "gridpath_viz_capacity_total_plot = viz.capacity_total_plot:main",
            "gridpath_viz_capacity_total_scenario_comparison_plot = viz.capacity_total_scenario_comparison_plot:main",
            "gridpath_viz_carbon_plot = viz.carbon_plot:main",
            "gridpath_viz_cost_plot = viz.cost_plot:main",
            "gridpath_viz_curtailment_hydro_heatmap_plot = viz.curtailment_hydro_heatmap_plot:main",
            "gridpath_viz_curtailment_variable_heatmap_plot = viz.curtailment_variable_heatmap_plot:main",
            "gridpath_viz_dispatch_plot = viz.dispatch_plot:main",
            "gridpath_viz_energy_plot = viz.energy_plot:main",
            "gridpath_viz_energy_target_plot = viz.energy_target_plot:main",
            "gridpath_viz_project_operations_plot = viz.project_operations_plot:main",
        ]
    },
)
