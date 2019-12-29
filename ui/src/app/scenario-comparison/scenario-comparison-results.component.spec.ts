import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioComparisonResultsComponent } from './scenario-comparison-results.component';

describe('ScenarioComparisonResultsComponent', () => {
  let component: ScenarioComparisonResultsComponent;
  let fixture: ComponentFixture<ScenarioComparisonResultsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScenarioComparisonResultsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioComparisonResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
