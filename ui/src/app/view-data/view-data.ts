/* tslint:disable:variable-name */
export class TimepointsTemporalRow {
  temporal_scenario_id: number;
  subproblem_id: number;
  stage_id: number;
  timepoint: number;
  horizon: number;
  period: number;
  number_of_hours_in_timepoint: number;
  previous_stage_timepoint_map: number;
  spinup_or_lookahead: number;
}
