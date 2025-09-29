import { Output, EventEmitter } from '@angular/core';
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

	//campi
	number?: number;
	title: string = '';
	longText: string = '';
	path: string = '';
	button: string = '';
	/*@Input() number?: number;
	@Input() title: string = '';
	@Input() longText: string = '';
	@Input() path: string = '';
	@Input() button: string = '';
	@Output() buttonClick = new EventEmitter<void>();*/

	private ngOnInit(){
		this.number = 0;
		this.title = "Cattura";
		this.longText = "Cattura: una volta che hai individuato la zona che ti interessa analizzare, puoi catturare l'immagine cliccando sul pulsante 'Cattura'.";
		this.path = "assets/cattura.svg";
		this.button = "Cattura";
	}

	onButtonClick() {
		//this.buttonClick.emit();
	}
}
