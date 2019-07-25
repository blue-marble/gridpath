from setuptools import find_packages, setup

setup(name='GridPath',
      version='0.1',
      description='Software for power-system planning',
      url='https://www.gridpath.io',
      maintainer='Blue Marble Analytics LLC',
      maintainer_email='gridpath@bluemarble.run',
      license='TBD',
      platforms=["any"],
      keywords=[
          'energy', 'electricity', 'power', 'renewables',
          'planning', 'operations'
      ],
      packages=find_packages(),
      install_requires=['Pyomo',  # Optimization modeling language
                        'pandas',
                        ],
      extras_require={
          'documentation': ["Sphinx"],  # Documentation
          'viz': ['matplotlib'],  # Visualization library
          'ui': ['eventlet',  # Async mode for SocketIO
                 'Flask',  # Local API server for UI
                 'Flask-RESTful',  # Flask extension for building REST APIs
                 'Flask-SocketIO'  # Client-server communication
                 ]
                      },
      include_package_data=True
      )
