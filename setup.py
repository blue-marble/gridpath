from setuptools import find_packages, setup

extras_doc = ['Sphinx']
extras_ui = [
    'eventlet',  # Async mode for SocketIO
     'Flask',  # Local API server for UI
     'Flask-RESTful',  # Flask extension for building REST APIs
     'Flask-SocketIO',  # Client-server communication
     'psutil'  # Process management
]
extras_all = extras_ui + extras_doc


setup(name='GridPath',
      version='0.1',
      description='Software for power-system planning',
      url='https://www.gridpath.io',
      maintainer='Blue Marble Analytics LLC',
      maintainer_email='info@gridpath.io',
      license='TBD',
      platforms=["any"],
      keywords=[
          'energy', 'electricity', 'power', 'renewables',
          'planning', 'operations'
      ],
      packages=find_packages(),
      install_requires=[
          'Pyomo',  # Optimization modeling language
          'pandas', # Data-processing
          'matplotlib'  # Visualization ibrary
      ],
      extras_require={
          'doc': extras_doc,
          'ui': extras_ui,
          'all': extras_all
      },
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'run_gridpath = gridpath.run_scenario:main',
              'run_gridpath_server = ui.server.run_server:main'
          ]
      }
      )
