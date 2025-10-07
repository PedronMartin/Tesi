import { Output, EventEmitter } from '@angular/core';
import {ChangeDetectionStrategy, Component} from '@angular/core';
import { CommonModule } from '@angular/common';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
import { SharedService } from '../../shared';
import { Router } from '@angular/router';

/**
 * @title Card with footer
 */

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

	//costruttore per il router delle pagine e per il servizio di condivisione dati
	constructor(private router: Router, private SharedService: SharedService) {};


	private ngOnInit(){
		this.number = 0;
		this.title = "Cattura";
		this.longText = "Cattura: una volta che hai individuato la zona che ti interessa analizzare, puoi catturare l'immagine cliccando sul pulsante 'Cattura'.";
		this.path = "assets/cattura.svg";
		this.button = "Cattura";
	}

	onButtonClick() {
		/* TODO: gestire il click sul bottone in base all'attuale contenuto della card */
		//notifico l'elemento shared per catturare i dati della mappa
		this.SharedService.triggerCattura();
	}
}
