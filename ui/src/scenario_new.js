const {ipcRenderer }= require('electron');
const Database = require('better-sqlite3');
const storage = require('electron-json-storage');


// Request to go back to scenario list
const backtoScenariosListButton =
    document.getElementById('backtoScenariosListButton');
backtoScenariosListButton.addEventListener(
    'click',
    (event) => {
        ipcRenderer.send('User-Requests-Index-View');
    }
);

//// Creating a new scenario ////
// Create the HTML string for a subscenario dropdowns form
const getSubscenarios = (db, table) => {
    const getSubscenariosSQL =
        db.prepare(`SELECT name FROM ${table};`);
    const subscenariosList = [];
    for (const subscenario of getSubscenariosSQL.iterate()) {
        subscenariosList.push(subscenario.name)
    }
    return subscenariosList
};

// TODO: need to catch exceptions
const insertNewScenariotoDatabase = (
    dbFilePath, scenarioName, projectPortfolio, opChars, loadProfile,
    fuelPrices
) => {
    console.log(dbFilePath);
    const db = new Database (dbFilePath, {fileMustExist: true});

    console.log(scenarioName, projectPortfolio, opChars, loadProfile, fuelPrices)
    const insertValuesStmnt = db.prepare(
        `INSERT INTO scenarios ( scenario_name, project_portfolio_scenario_id, 
        project_operational_chars_scenario_id, load_scenario_id, 
        fuel_price_scenario_id) 
        VALUES (?, ?, ?, ?, ?);`
    );

    insertValuesStmnt.run(
        scenarioName, projectPortfolio, opChars,
        loadProfile, fuelPrices
    );

    db.close();
};

// We need to get the user-defined database file path, so all functionality
// dependent on access to the database is inside a storage.get()
storage.get(
    'dbFilePath',
    (error, data) => {
        if (error) throw error;
        const dbFilePath = data['dbFilePath'][0];

        // Get the subscenario names for the dropdowns from the database
        const db = new Database (dbFilePath, {fileMustExist: true});

        const portfolioSubscenarios =
            getSubscenarios(db,'subscenarios_project_portfolios');
        const opCharsSubscenarios =
            getSubscenarios(db,'subscenarios_project_operational_chars');
        const loadProfileSubscenarios =
            getSubscenarios(db,'subscenarios_system_load');
        const fuelPriceSubscenarios =
            getSubscenarios(db,'subscenarios_project_fuel_prices');

        db.close();

        // Create the new scenario view HTML
        // TODO: HTML creation below is ugly and needs refactoring
        let subscenarioDropdownHTML =
            `<div>
                <label for="newScenarioName">Scenario Name: </label>
                <input type="text" id="newScenarioName" placeholder="New scenario name">
            </div>
            <div id="projectPortfolioDropdown">
            <label for="projPortfolio">Portfolio: </label>
            <select id="projPortfolio">`;

        Object.keys(portfolioSubscenarios).forEach(
                (key) => {
                    console.log(portfolioSubscenarios[key]);
                    subscenarioDropdownHTML +=
                        `<option>${portfolioSubscenarios[key]}</option>`;
                }
        );

        subscenarioDropdownHTML +=
            `</select>
            </div>
            <div id="opCharsDropdown">
            <label for="opChars">Operating Characteristics: </label>
            <select id="opChars">`;

        Object.keys(opCharsSubscenarios).forEach(
                (key) => {
                    console.log(opCharsSubscenarios[key]);
                    subscenarioDropdownHTML +=
                        `<option>${opCharsSubscenarios[key]}</option>`;
                }
        );

        subscenarioDropdownHTML +=
            `</select>
            </div>
            <div id="loadProfileDropdown">
            <label for="loadProfile">Load Profile: </label>
            <select id="loadProfile">`;

        Object.keys(loadProfileSubscenarios).forEach(
                (key) => {
                    console.log(loadProfileSubscenarios[key]);
                    subscenarioDropdownHTML +=
                        `<option>${loadProfileSubscenarios[key]}</option>`;
                }
        );

        subscenarioDropdownHTML +=
            `</select>
            </div>
            <div id="fuelPricesDropdown">
            <label for="fuelPrices">Fuel Prices: </label>
            <select id="fuelPrices">`;

        Object.keys(fuelPriceSubscenarios).forEach(
                (key) => {
                    console.log(fuelPriceSubscenarios[key]);
                    subscenarioDropdownHTML +=
                        `<option>${fuelPriceSubscenarios[key]}</option>`;
                }
        );

        subscenarioDropdownHTML +=
            `</select>
            </div>
            <button class="button">Save scenario</button>`;

        console.log(subscenarioDropdownHTML);

        document.getElementById('newScenarioDetailForm').innerHTML =
            subscenarioDropdownHTML;

        // Listen for submission of the new scenario form and insert the
        // scenario into database
        // TODO: what should happen when the user clicks save -- show scenario detail,
        //  return to scenario list, etc.?
        document.getElementById(
            'newScenarioDetailForm'
        ).addEventListener(
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
                const loadProfile = document.getElementById(
                    'loadProfile'
                ).value;
                const fuelPrices = document.getElementById(
                    'fuelPrices'
                ).value;

                // Open the database
                const db = new Database (dbFilePath, {fileMustExist: true});

                // For now, we need to insert the respective subscenario IDs
                // in the scenario table, so get them here
                const getProjPortfolioIdSQL = db.prepare(
                    `SELECT project_portfolio_scenario_id 
                    FROM subscenarios_project_portfolios
                    WHERE name = ?;`
                ).get(projPortfolio);
                const projPortfolioId =
                    getProjPortfolioIdSQL.project_portfolio_scenario_id;

                const getProjOpCharsIdSQL = db.prepare(
                    `SELECT project_operational_chars_scenario_id 
                    FROM subscenarios_project_operational_chars
                    WHERE name = ?;`
                ).get(opChars);
                const opCharsId =
                    getProjOpCharsIdSQL.project_operational_chars_scenario_id;

                const getloadProfileIdSQL = db.prepare(
                    `SELECT load_scenario_id 
                    FROM subscenarios_system_load
                    WHERE name = ?;`
                ).get(loadProfile);
                const loadProfileId =
                    getloadProfileIdSQL.load_scenario_id;

                const getFuelPricesIdSQL = db.prepare(
                    `SELECT fuel_price_scenario_id 
                    FROM subscenarios_project_fuel_prices
                    WHERE name = ?;`
                ).get(fuelPrices);
                const fuelPricesId =
                    getFuelPricesIdSQL.fuel_price_scenario_id;

                // Insert values into database
                insertNewScenariotoDatabase(
                    dbFilePath, scenarioName, projPortfolioId, opCharsId,
                    loadProfileId, fuelPricesId
                );

                // Close the database
                db.close();

                // Finally, switch to scenario detail view for new scenario
                const sendScenarioName = (scenarioName) => {
                   console.log(
                       `Switch to detail view for new scenario ${scenarioName}`
                   );
                   ipcRenderer.send(
                       'User-Requests-Scenario-Detail', scenarioName
                   );
                };
            }
        );
    }
);
