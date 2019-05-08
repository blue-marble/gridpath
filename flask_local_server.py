from flask import Flask
from flask import render_template
import os
import pyutilib.subprocess.GlobalData

# Turn off signal handlers (in order to be able to spawn solvers from a
# Pyomo running in a thread)
# See: https://groups.google.com/forum/#!searchin/pyomo-forum
# /flask$20main$20thread%7Csort:date/pyomo-forum/TRwSIjQMtHI
# /e41wDAkPCgAJ and https://github.com/PyUtilib/pyutilib/issues/31
#
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False

app = Flask(__name__)

# @app.route('/hello/')
# @app.route('/hello/<name>')
# def hello(name=None):
#     return render_template('hello.html', name=name)
#
#
# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=8000)


@app.route('/')
def run_scenario():

    os.chdir('/Users/ana/dev/gridpath-ui-dev/')
    import run_scenario
    run_scenario.main(
        args=['--scenario', 'test', '--scenario_location',
              'examples', '--solver', 'cplex']
    )
    return("Scenario completed")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8000', debug=True)
