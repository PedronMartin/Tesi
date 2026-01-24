import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
import {SharedService} from '../../shared';
import {Router} from '@angular/router';

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
	@Input() cardId: number = 0;
	number?: number;
	title: string = '';
	longText: string = '';
	path: string = '';
	button: string = '';

	//costruttore per il router delle pagine e per il servizio di condivisione dati
	constructor(private router: Router, private SharedService: SharedService) {};


	ngOnInit(){
		if(this.cardId == 0) this.setCard1();
		else if(this.cardId == 3) this.setCard3();
		else this.setCard2();
	}

	private setCard1(){
		this.number = this.cardId + 1;
		this.title = "Cattura";
		this.longText = "Cattura: una volta che hai individuato la zona che ti interessa analizzare, puoi catturare l'immagine cliccando sul pulsante 'Cattura'.";
		this.path = "assets/cattura.svg";
		this.button = "Cattura";
	}

	private setCard2(){
		this.number = this.cardId + 1;
		this.title = "Analizza";
		this.longText = "Analizza: dopo aver selezionato l'area di interesse, puoi richiedere l'analisi";
		this.path = "assets/calcola.svg";
		this.button = "Analizza";
	}

	private setCard3(){
		this.number = this.cardId + 1;
		this.title = "Estrai";
		this.longText = "Estrai: una volta completata l'analisi, puoi estrarre i dati ottenuti in formato GeoJson.";
		this.path = "assets/estrai.svg";
		this.button = "Estrai";
	}

	onButtonClick() {
		//notifico l'elemento shared per catturare i dati della mappa
		if(this.cardId == 0)
			this.SharedService.triggerCattura();
		//estraggo i dati
		else if(this.cardId == 3)
			//delega al servizio condiviso che possiede i dati
        	this.SharedService.downloadData();
		else
			this.SharedService.catturaPoligono$.next();
	}
}