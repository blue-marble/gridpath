import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioRunLogComponent } from './scenario-run-log.component';

describe('ScenarioRunLogComponent', () => {
  let component: ScenarioRunLogComponent;
  let fixture: ComponentFixture<ScenarioRunLogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScenarioRunLogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioRunLogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
