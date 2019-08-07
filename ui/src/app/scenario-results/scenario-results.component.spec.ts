import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioResultsComponent } from './scenario-results.component';

describe('ScenarioResultsComponent', () => {
  let component: ScenarioResultsComponent;
  let fixture: ComponentFixture<ScenarioResultsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScenarioResultsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
