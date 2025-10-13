import {Injectable} from '@angular/core';
import * as S from "./server-contacter";
import {Subject} from 'rxjs';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class SharedService {
  /*TODO: vedere come tipizzare meglio in quanto non so come effettivamente passare i dati per caricare la stessa mappa*/
  private CaptureZone: any[] = [];
  private PolygonData: number[][] = [];
  private responseData: any;

  //Subject per notificare la richiesta di cattura (notificaCattura per la prima mappa, catturaPoligono per la seconda)
  public notificaCattura$ = new Subject<void>();
  public catturaPoligono$ = new Subject<void>();

  public onPolygonReady: (() => void) | null = null;
  constructor(
    private serverContact: S.ServerContacter,
    private router: Router
  ) {}

  setCaptureZone(val: any) {
    this.CaptureZone = val;
  }

  getCaptureZone() {
    return this.CaptureZone;
  }

  setPolygonData(val: any [][]) {
    this.PolygonData = val;
  }

  getPolygonData() {
    return this.PolygonData;
  }

  // metodo per notificare la mappa
  triggerCattura() {
    this.notificaCattura$.next();
  }

  //metodo per ricevere i risultati del calcolo dal server
  getResponseData() {
    return this.responseData;
  }

  // metodo per inviare la richiesta di calcolo al server
  serverRequest() {
    this.serverContact.runFullAnalysis(this.PolygonData).subscribe(
      response => {
        this.responseData = response;
        console.log("Risposta dal server:", response);
        setTimeout(() => {
          this.router.navigate(['/calcolo']);
        }, 100);
      },
      error => console.error("Errore:", error)
    );
  }

  /* TODO:
  si potrebbe aggiungere in home page un riquadro sotto la card2 per mostrare l'avanzamento della richiesta al server
  ed eventuali errori generati dalla richiesta. Per esempio, quando richiesto il calcolo bisogna ri-andare a caricare i dati della mappa
  dato che il poligono è modificabile. Inoltre, aggiungere un testo che esplicita il fatto che il calcolo avviene sui dati della seconda mappa e non della prima
  */
}