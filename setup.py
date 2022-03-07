from setuptools import find_packages, setup

# Get version
version = {}
with open("./version.py") as fp:
    exec(fp.read(), version)

# Set up extras
extras_doc = [
    "Sphinx==4.0.2",
    "sphinx-argparse==0.2.5",
    "numpy==1.21.5"  # temporarily require v1.21.5 because v1.22 is not available on
    # readthedocs and build fails otherwise
]
extras_ui = [
    "eventlet==0.31.0",  # Async mode for SocketIO
    "Flask==2.0.1",  # Local API server for UI
    "Flask-RESTful==0.3.9",  # Flask extension for building REST APIs
    "Flask-SocketIO==4.3.2",  # Flask client-server communication
    "psutil==5.8.0",  # Process management
    "python-socketio[client]<5,>=4.3.0",  # SocketIO Python client
]
extras_black = ["black"]

extras_coverage = [
    "coverage",  # test coverage
    "coveralls",  # automated coverage results
]
extras_all = extras_ui + extras_doc + extras_black + extras_coverage

setup(
    name="GridPath",
    version=version["__version__"],
    description="A versatile simulation and optimization platform for "
    "power-system planning and operations.",
    url="https://www.gridpath.io",
    maintainer="Blue Marble Analytics LLC",
    maintainer_email="info@gridpath.io",
    license="Apache v2",
    platforms=["MacOS", "Windows"],
    keywords=["energy", "electricity", "power", "renewables", "planning", "operations"],
    packages=find_packages(),
    install_requires=[
        "Pyomo==6.3.0",  # Optimization modeling language
        "pandas==1.2.5",  # Data-processing
        "bokeh==2.2.3",  # Visualization library (required - see #779)
        "pscript==0.7.5",  # Python to JavaScript compiler (for viz)
        "networkx==2.5.1",  # network package for DC OPF
        "pyutilib==6.0.0",  # used for solver temp file management
    ],
    extras_require={
        "doc": extras_doc,
        "ui": extras_ui,
        "all": extras_all,
        "coverage": extras_coverage,
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "gridpath_run = gridpath.run_scenario:main",
            "gridpath_run_e2e = gridpath.run_end_to_end:main",
            "gridpath_get_inputs = gridpath.get_scenario_inputs:main",
            "gridpath_import_results = " "gridpath.import_scenario_results:main",
            "gridpath_process_results = gridpath.process_results:main",
            "gridpath_validate = gridpath.validate_inputs:main",
            "gridpath_run_server = ui.server.run_server:main",
            "gridpath_run_queue_manager = ui.server.run_queue_manager:main",
        ]
    },
)
