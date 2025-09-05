import {ChangeDetectionStrategy, Component} from '@angular/core';
import { CommonModule } from '@angular/common';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';

/**
 * @title Card with footer
 */
import { Input } from '@angular/core';

@Component({
  selector: 'instructionCard',
  templateUrl: './instruction-card.html',
  styleUrls: ['./instruction-card.css'],
  imports: [MatCardModule, MatChipsModule, MatProgressBarModule, CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InstructionCard {
  @Input() number?: number;
  @Input() title: string = '';
  @Input() longText: string = '';
  @Input() path: string = '';
}