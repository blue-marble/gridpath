const {ipcRenderer }= require('electron');
const Database = require('better-sqlite3');
const storage = require('electron-json-storage');

// Request to go back to scenario list
const backtoScenariosListButton =
    document.getElementById(('backtoScenariosListButton'));
backtoScenariosListButton.addEventListener(
    'click', function (event) {
        ipcRenderer.send("User-Requests-Index-View");
    }
);


// Listen for submission of the new scenario form and insert into database
// TODO: what should happen when the user clicks save -- show scenario detail,
//  return to scenario list, etc.?
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

        // We need to get the user-defined database file path
        storage.get(
            'dbFilePath',
            function(error, data) {
                if (error) throw error;
                const dbFilePath = data['dbFilePath'][0];

                // Insert values into database
                insertNewScenariotoDatabase(
                    dbFilePath, scenarioName, projPortfolio, opChars,
                    loadLevel, fuelPrices
                );

                }
            );
    });

// TODO: need to catch exceptions
function insertNewScenariotoDatabase(
    dbFilePath, scenario_name, project_portfolio, operating_characteristics,
    load_level, fuel_prices
) {
    console.log(dbFilePath);
    const db = new Database (dbFilePath, {fileMustExist: true});

    const insertValuesStmnt = db.prepare(
        "INSERT INTO scenarios ( scenario_name, project_portfolio_scenario_id, " +
        "project_operational_chars_scenario_id, load_scenario_id, " +
        "fuel_price_scenario_id)" +
        " VALUES (?, ?, ?, ?, ?);");

    insertValuesStmnt.run(
        scenario_name, project_portfolio, operating_characteristics,
        load_level, fuel_prices
    );

    db.close();

}
