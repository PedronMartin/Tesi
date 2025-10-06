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
  private featureGroup: any;

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
        setTimeout(() => {
          this.drawableMap();
          this.loadCaptureData(mapDiv);
        }, 200);
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

    if (isPlatformBrowser(this.platformId)) {
      import('leaflet').then(L => {
        if (!mapDiv) {
          console.error('Impossibile trovare il div della mappa con id', this.mapId);
          return;
        }
        this.L = L;
        this.map = L.map(mapDiv, {
          center: [45.464664, 9.188540],
          zoom: 13
        });
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 30
        }).addTo(this.map);
        this.map.setMaxZoom(30);
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

  private drawableMap(): void {
    if (isPlatformBrowser(this.platformId)) {
      import('leaflet-draw').then(() => {
        this.featureGroup = new this.L.FeatureGroup();
        this.map.addLayer(this.featureGroup);
        console.log('FeatureGroup creato:', this.featureGroup);

        // Se ci sono dati di cattura, crea il rettangolo e aggiungilo al featureGroup
        const bounds = MapLayerComponent.captureData[0];
        console.log('Bounds in drawableMap:', bounds);
        if (bounds) {
          const rectangle = this.L.rectangle(bounds, { color: "#080807ff", weight: 5, opacity: 0.4 });
          this.featureGroup.addLayer(rectangle);
          console.log('Rettangolo creato e aggiunto:', rectangle);
        } else {
          console.warn('Nessun bounds valido per rettangolo');
        }

        const drawControl = new this.L.Control.Draw({
          draw: {
            polygon: false,
            polyline: false,
            circle: false,
            marker: false,
            circlemarker: false,
            rectangle: true
          },
          edit: {
            featureGroup: this.featureGroup //il gruppo dove hai aggiunto il rettangolo
          }
        });
        this.map.addControl(drawControl);
        console.log('DrawControl aggiunto:', drawControl);
      });
    }
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
    // Ora la creazione del rettangolo è gestita solo in drawableMap
    this.map.on('draw:edited', (e: any) => {
      // e.layers contiene i layer modificati
      e.layers.eachLayer((layer: any) => {
      // layer.getBounds() ti dà i nuovi bounds
      });
    });
  }
}