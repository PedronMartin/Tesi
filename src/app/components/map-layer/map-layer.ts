import { Component, AfterViewInit, PLATFORM_ID, Inject, Input } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { SharedService } from '../../shared';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-map-layer',
  templateUrl: './map-layer.html',
  styleUrls: ['./map-layer.css']
})
export class MapLayerComponent implements AfterViewInit {

  //campi
  @Input() mapId: string = 'map';
  private static captureData: any[] = [];
  private L: any;

  //sottoscrizione eventlistener per la cattura
  private catturaSub!: Subscription;
  private map: any;
  //servizio di condivisione dati
  constructor(@Inject(PLATFORM_ID) private platformId: Object, private SharedService: SharedService) { }

  ngOnInit() {
    this.catturaSub = this.SharedService.notificaCattura$.subscribe(() => {
      let mapDiv: HTMLElement | null = document.getElementById(this.mapId);
      if(this.mapId == 'map1') {
        MapLayerComponent.captureData = [];
        MapLayerComponent.captureData = this.onCapture();
      }
      else {
        this.map.eachLayer((layer: any) => {
          //rimuovi tutti i layer tranne il tileLayer (quello di base)
          if (!(layer instanceof this.L.TileLayer))
            this.map.removeLayer(layer);
        });
        this.loadCaptureData(mapDiv);
      }
    });
  }

  ngOnDestroy() {
    if (this.catturaSub) {
      this.catturaSub.unsubscribe();
    }
  }

  //appena caricato il layer della mappa, andiamo a capire di quale si tratta
  ngAfterViewInit(): void {
    let mapDiv: HTMLElement | null = null;
    if (isPlatformBrowser(this.platformId)) {
      mapDiv = document.getElementById(this.mapId);
      this.initializeMap(mapDiv);
    }
  }

  private initializeMap(mapDiv: HTMLElement | null): void {

   /* //rimuove la mappa precedente se esiste
    if(this.map && typeof this.map.remove === 'function')
        this.map.remove();

      //se il div ha già una mappa associata, la rimuovo (caso edge)
      if((mapDiv as any)._leaflet_id) {
        try {
          L.map(mapDiv).remove();
        } catch (e) {
          //ignora errori se la mappa non esiste
        }
      }*/

    if (isPlatformBrowser(this.platformId)) {
      import('leaflet').then(L => {
        if (!mapDiv) {
          console.error('Impossibile trovare il div della mappa con id', this.mapId);
          return;
        }
        this.L = L; //importo Leaflet globalmente
        this.map = L.map(mapDiv, {
          center: [45.464664, 9.188540],
          zoom: 13
        });
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 30
        }).addTo(this.map);
        this.map.setMaxZoom(30);
        //carico i dati solo per map2
        /*la versione precedente con lo switch case che smistava e ordinava la chiamate non funziona in quanto
          non verificava che la seconda mappa fosse adeguatamente caricata prima del load dei dati precedenti
        */
        if (this.mapId === 'map2') {
          this.loadCaptureData(mapDiv);
        }
      });
    }
  }

    /*
    TODO: vedere se esiste modo di potenziare il rendering della mappa per caricare più veloce spostamenti dell'utente e zoom vari
    */

  //funzione per catturare i dati della mappa
  private onCapture(): any[] {
    const datiCatturati = [];
    // Non serve recuperare il div, usiamo direttamente l'istanza della mappa
    if (isPlatformBrowser(this.platformId) && this.map) {
      datiCatturati[0] = (this.map as any).getBounds();
      datiCatturati[1] = (this.map as any).getCenter();
      datiCatturati[2] = (this.map as any).getZoom();
    } else {
      datiCatturati[0] = null;
      datiCatturati[1] = null;
      datiCatturati[2] = null;
      console.warn(`Elemento mappa con id '${this.mapId}' non trovato o 'getBounds' non disponibile.`);
    }
    console.log(datiCatturati);
    return datiCatturati;
  }

  //funzione per caricare i dati nella mappa di pre-calcolo
  private loadCaptureData(mapDiv: HTMLElement | null): void {
    if(isPlatformBrowser(this.platformId) && this.map &&
      typeof this.map.fitBounds == 'function' && MapLayerComponent.captureData[0]) {
        if(isPlatformBrowser(this.platformId) && this.map &&
          typeof this.map.fitBounds === 'function' && MapLayerComponent.captureData[0]) {
          setTimeout(() => {
            (this.map as any).fitBounds(MapLayerComponent.captureData[0]);
            setTimeout(() => {
              const minZoom = this.map.getMinZoom ? this.map.getMinZoom() : 1;
              const newZoom = Math.max(minZoom, this.map.getZoom() - 1);
              (this.map as any).setZoom(newZoom);
            }, 300);
          }, 100);
        } else
          console.warn(`Elemento mappa con id '${this.mapId}' non trovato, dati non validi o 'fitBounds' non disponibile.`);
    }

    this.setPerimeters();
  }

  private setPerimeters() {
    if (isPlatformBrowser(this.platformId) && this.map) {
      //crea rettangolo che traccia il perimetro della zona catturata
      const bounds = MapLayerComponent.captureData[0];
      if (bounds) {
        const rectangle = this.L.rectangle(bounds, { color: "#080807ff", weight: 5 });
        rectangle.addTo(this.map);
      } else
        console.warn("Dati di cattura non disponibili per tracciare il perimetro.");
    }
  }
}