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
  button: ResultsButton;
}

export class FormControlOptions {
  formControlName: string;
  formControlOptions: [];
}
