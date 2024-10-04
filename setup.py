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
extras_ui = [
    "eventlet==0.33.3",  # Async mode for SocketIO
    "Flask==2.0.1",  # Local API server for UI
    "Flask-RESTful==0.3.9",  # Flask extension for building REST APIs
    "Flask-SocketIO==4.3.2",  # Flask client-server communication; see #772
    "psutil==5.9.6",  # Process management
    "python-socketio[client]<5,>=4.3.0",  # SocketIO Python client; see #772
    "Werkzeug==2.0.2",  # See #903
    "dnspython==2.4.2",  # Avoids potential eventlet version mismatch
]
extras_black = ["black"]

extras_coverage = [
    "coverage",  # test coverage
    "coveralls",  # automated coverage results
]

extras_gurobi = ["gurobipy"]  # Gurobi Python interface

extras_all = extras_ui + extras_doc + extras_black + extras_coverage + extras_gurobi

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
        "Pyomo==6.8.0",  # Optimization modeling language
        "pandas==2.2.1",  # Data-processing
        "bokeh==2.2.3",  # Visualization library (required - see #779)
        "pscript==0.7.5",  # Python to JavaScript compiler (for viz)
        "networkx==3.1",  # network package for DC OPF
        "PyUtilib==6.0.0",  # used for solver temp file management
        "Jinja2==3.0.3",  # bokeh dependency; see #904
        "dill==0.3.7",  # pickling
    ]
    + extras_ui,
    extras_require={
        "doc": extras_doc,
        "all": extras_all,
        "coverage": extras_coverage,
        "gurobi": extras_gurobi,
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
            "gridpath_run_ra_toolkit = db.utilities.ra_toolkit.run_ra_toolkit:main",
        ]
    },
)
