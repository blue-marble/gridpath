/* tslint:disable:variable-name */

export class ScenarioResultsTable {
  table: string;
  caption: string;
  columns: [];
  rowsData: [];
}

// TODO: what is the json plot's type?
export class ScenarioResultsPlot {
  plotJSON: any;
}

export class ResultsOptions {
  loadZoneOptions: [];
  rpsZoneOptions: [];
  carbonCapZoneOptions: [];
  periodOptions: [];
  subproblemOptions: [];
  stageOptions: [];
  projectOptions: [];
  commitProjectOptions: [];
}

export class IncludedPlotFormBuilderAPI {
  'plotType': string;
  'caption': string;
  'loadZone': [] | string;
  'carbonCapZone': [] | string;
  'rpsZone': [] | string;
  'period': [] | string;
  'horizon': [] | string;
  'startTimepoint': [] | string;
  'endTimepoint': [] | string;
  'subproblem': [] | string;
  'stage': [] | string;
  'project': [] | string;
  'commitProject': [] | string;
}
