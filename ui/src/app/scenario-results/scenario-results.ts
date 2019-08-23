/* tslint:disable:variable-name */

// TODO: consolidate with ViewDataTable (view-data.ts)?
import {FormGroup} from '@angular/forms';

export class ScenarioResults {
  ngIfKey: string;
  caption: string;
  columns: [];
  rowsData: [];
}

export class ResultsButton {
  name: string;
  ngIfKey: string;
  caption: string;
}

export class ResultsForm {
  formGroup: FormGroup;
  selectForms: FormControlOptions[];
  yMaxFormControlName: string;
  button: ResultsButton;
}

export class FormControlOptions {
  formControlName: string;
  formControlOptions: [];
}

// TODO: what is the json plot's type?
export class PlotAPI {
  plotJSON: object;
}

export class ResultsOptions {
  loadZoneOptions: [];
  horizonOptions: [];
  stageOptions: [];
}
