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
  periodOptions: [];
  horizonOptions: [];
  timepointOptions: [];
  stageOptions: [];
  projectOptions: [];
}

export class IncludedPlotFormBuilderAPI {
  'plotType': string;
  'caption': string;
  'loadZone': [] | string;
  'period': [] | string;
  'horizon': [] | string;
  'timepoint': [] | string;
  'stage': [] | string;
  'project': [] | string;
}
