import { TestBed } from '@angular/core/testing';

import { ScenariosService } from './scenarios.service';

describe('ScenariosService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ScenariosService = TestBed.get(ScenariosService);
    expect(service).toBeTruthy();
  });
});
