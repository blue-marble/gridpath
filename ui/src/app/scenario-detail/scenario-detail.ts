export class ScenarioDetail {
  uiTableNameInDB: string;
  scenarioDetailTableCaption: string;
  scenarioDetailTableRows: ScenarioDetailTableRow[];
}

export class ScenarioDetailTableRow {
  uiRowNameInDB: string;
  rowCaption: string;
  rowValue: string;
  inputTable: string;
}
