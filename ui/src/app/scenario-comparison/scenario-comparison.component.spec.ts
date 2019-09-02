import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioComparisonComponent } from './scenario-comparison.component';

describe('ScenarioComparisonComponent', () => {
  let component: ScenarioComparisonComponent;
  let fixture: ComponentFixture<ScenarioComparisonComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScenarioComparisonComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioComparisonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
