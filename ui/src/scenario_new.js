const {ipcRenderer }= require('electron');
const Database = require('better-sqlite3');
const path = require('path');

// Request to go back to scenario list
const BacktoScenariosListButton =
    document.getElementById(('BacktoScenariosListButton'));
BacktoScenariosListButton.addEventListener(
    'click', function (event) {
        ipcRenderer.send("User-Requests-Index-View");
    }
);


// Listen for submission of the new scenario form and insert into database
document.getElementById('newScenarioDetailForm').addEventListener(
    'submit', (event) => {
        // prevent default refresh functionality of forms (?)
        event.preventDefault();

        // Get the user-specified input values
        const scenarioName = document.getElementById(
            'newScenarioName'
        ).value;
        const projPortfolio = document.getElementById(
            'projPortfolio'
        ).value;
        const opChars = document.getElementById(
            'opChars'
        ).value;
        const loadLevel = document.getElementById(
            'loadProfile'
        ).value;
        const fuelPrices = document.getElementById(
            'fuelPrices'
        ).value;

        // Insert values into database
        insertNewScenariotoDatabase(
            scenarioName, projPortfolio, opChars, loadLevel, fuelPrices
        );
        // send call to main process to return us to scenario list view
        // TODO: actually we don't need this, do we
        ipcRenderer.send(
            'Save-New-Scenario'
        )
    });

// TODO: need to catch exceptions
function insertNewScenariotoDatabase(
    scenario_name, project_portfolio, operating_characteristics, load_level,
    fuel_prices
) {
    const io_file = path.join(__dirname, "../db/io.db");
    const io = new Database (io_file, {fileMustExist: true});

    const insertValuesStmnt = io.prepare(
        "INSERT INTO scenarios ( scenario_name, project_portfolio_scenario_id, " +
        "project_operational_chars_scenario_id, load_scenario_id, " +
        "fuel_price_scenario_id)" +
        " VALUES (?, ?, ?, ?, ?);");

    insertValuesStmnt.run(
        scenario_name, project_portfolio, operating_characteristics,
        load_level, fuel_prices
    );

    io.close();

}
