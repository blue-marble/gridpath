import { TestBed } from '@angular/core/testing';

import { ScenarioDetailService } from './scenario-detail.service';

describe('ScenarioDetailService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ScenarioDetailService = TestBed.get(ScenarioDetailService);
    expect(service).toBeTruthy();
  });
});
