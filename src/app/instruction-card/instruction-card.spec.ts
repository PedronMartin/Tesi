import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InstructionCard } from './instruction-card';

describe('InstructionCard', () => {
  let component: InstructionCard;
  let fixture: ComponentFixture<InstructionCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InstructionCard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InstructionCard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
