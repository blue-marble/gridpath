from setuptools import find_packages, setup

# Get version
version = {}
with open("./version.py") as fp:
    exec(fp.read(), version)

# Set up extras
extras_doc = [
    "Sphinx==3.3.1",
    "sphinx-argparse==0.2.5"
]
extras_ui = [
    "eventlet==0.29.1",  # Async mode for SocketIO
    "Flask==1.1.2",  # Local API server for UI
    "Flask-RESTful==0.3.8",  # Flask extension for building REST APIs
    "Flask-SocketIO==4.3.1",  # Flask client-server communication
    "psutil==5.7.3",  # Process management
    "python-socketio[client]==4.6.0",  # SocketIO Python client
]
extras_all = extras_ui + extras_doc


setup(name="GridPath",
      version=version["__version__"],
      description="Software for power-system planning",
      url="https://www.gridpath.io",
      maintainer="Blue Marble Analytics LLC",
      maintainer_email="info@gridpath.io",
      license="TBD",
      platforms=["any"],
      keywords=[
          "energy", "electricity", "power", "renewables",
          "planning", "operations"
      ],
      packages=find_packages(),
      install_requires=[
          "Pyomo==5.7.1",  # Optimization modeling language
          "pandas==1.1.4",  # Data-processing
          "bokeh==2.2.3",  # Visualization library
          "pscript==0.7.4",  # Python to JavaScript compiler (for visualization)
          "networkx==2.5"  # network package for DC OPF
      ],
      extras_require={
          "doc": extras_doc,
          "ui": extras_ui,
          "all": extras_all
      },
      include_package_data=True,
      entry_points={
          "console_scripts": [
              "gridpath_run = gridpath.run_scenario:main",
              "gridpath_run_e2e = gridpath.run_end_to_end:main",
              "gridpath_get_inputs = gridpath.get_scenario_inputs:main",
              "gridpath_import_results = "
              "gridpath.import_scenario_results:main",
              "gridpath_process_results = gridpath.process_results:main",
              "gridpath_validate = gridpath.validate_inputs:main",
              "gridpath_run_server = ui.server.run_server:main",
              "gridpath_run_queue_manager = ui.server.run_queue_manager:main"
          ]
      }
      )
