import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SharedService {
  /*TODO: vedere come tipizzare meglio in quanto non so come effettivamente passare i dati per caricare la stessa mappa*/
  private CaptureZone = [];

  //Subject per notificare la richiesta di cattura
  public catturaPerimetro$ = new Subject<void>();

  set(val: any) {
    this.CaptureZone = val;
    console.log('Dati catturati e salvati nel servizio di condivisione:', this.CaptureZone);
  }

  get() {
    return this.CaptureZone;
  }

  // Metodo per notificare la mappa
  triggerCattura() {
    this.catturaPerimetro$.next();
  }
}
