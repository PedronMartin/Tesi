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
  private drawControl: any;

  //campi
  @Input() mapId: string = 'map';
  private static captureData: any[] = [];
  private static polygonData: number[][] = [];
  private L: any;
  private featureGroup: any;
  private map: any;

  //sottoscrizione eventlistener per le catture
  private catturaSub!: Subscription;
  private catturaPoligonoSub!: Subscription;
  //servizio di condivisione dati
  constructor(@Inject(PLATFORM_ID) private platformId: Object, private SharedService: SharedService) { }

  ngOnInit() {
    this.catturaSub = this.SharedService.notificaCattura$.subscribe(() => {
      let mapDiv: HTMLElement | null = document.getElementById(this.mapId);
      if(this.mapId == 'map1') {
        MapLayerComponent.captureData = [];
        MapLayerComponent.captureData = this.onCapture();
        // Nessuna chiamata a drawableMap per map1
      }
      //map2
      else {
        this.map.eachLayer((layer: any) => {
          //rimuovi tutti i layer tranne il tileLayer (quello di base)
          if (!(layer instanceof this.L.TileLayer))
            this.map.removeLayer(layer);
        });
        // Rimuovo il vecchio drawControl se esiste
        if (this.drawControl) {
          this.map.removeControl(this.drawControl);
          this.drawControl = null;
        }
        // Chiamo subito drawableMap dopo aver aggiornato i dati
        this.loadCaptureData(mapDiv);
      }
    });

    this.catturaPoligonoSub = this.SharedService.catturaPoligono$.subscribe(() => {
      if(this.mapId == 'map2') {
        MapLayerComponent.polygonData = [];
        MapLayerComponent.polygonData = this.capturePolygon();
        this.SharedService.setPolygonData(MapLayerComponent.polygonData);
        this.SharedService.serverRequest();
      }
    });
  }

  ngOnDestroy() {
    if(this.catturaSub) this.catturaSub.unsubscribe();
    if(this.catturaPoligonoSub) this.catturaPoligonoSub.unsubscribe();
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
          center: [46.06001421239969, 11.114192721424503],
          zoom: 13
        });
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 30
        }).addTo(this.map);
        this.map.setMaxZoom(30);

        if (this.mapId === 'map2')
          this.loadCaptureData(mapDiv);
        else {
          //search-bar per map1
          if (isPlatformBrowser(this.platformId)) {
            import('leaflet-search').then(() => {
              const searchControl = new (this.L.Control as any).Search({
                url: 'https://nominatim.openstreetmap.org/search?format=json&q={s}',
                propertyName: 'display_name',   //campo del json con il nome
                marker: false,                  //disabilita il marker automatico
                propertyLoc: ['lat','lon'],     //campi lat e lon per la posizione
                autoCollapse: true,             //chiude la barra di ricerca dopo il risultato
                minLength: 2                    //min caratteri da inserire prima della ricerca
              });
              this.map.addControl(searchControl);
            });
          }
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
    if (isPlatformBrowser(this.platformId) && this.map) {
      // Se non ci sono bounds, uso quelli della mappa corrente
      const bounds = (this.map as any).getBounds();
      datiCatturati[0] = bounds ? bounds : null;
      datiCatturati[1] = (this.map as any).getCenter();
      datiCatturati[2] = (this.map as any).getZoom();
    } else {
      datiCatturati[0] = null;
      datiCatturati[1] = null;
      datiCatturati[2] = null;
      console.warn(`Elemento mappa con id '${this.mapId}' non trovato o 'getBounds' non disponibile.`);
    }
    return datiCatturati;
  }

  private drawableMap(): void {
    if (isPlatformBrowser(this.platformId)) {
      import('leaflet-draw').then(() => {
        this.featureGroup = new this.L.FeatureGroup();
        this.map.addLayer(this.featureGroup);
        const bounds = MapLayerComponent.captureData[0];
            if (bounds) {
              // Ottieni i quattro angoli dai bounds
              const sw = bounds.getSouthWest();
              const nw = bounds.getNorthWest ? bounds.getNorthWest() : this.L.latLng(bounds.getNorth(), bounds.getWest());
              const ne = bounds.getNorthEast();
              const se = bounds.getSouthEast ? bounds.getSouthEast() : this.L.latLng(bounds.getSouth(), bounds.getEast());
              // Leaflet standard non ha getNorthWest/getSouthEast, quindi li calcolo manualmente
              const north = bounds.getNorth();
              const south = bounds.getSouth();
              const east = bounds.getEast();
              const west = bounds.getWest();
              const points = [
                this.L.latLng(north, west), // NW
                this.L.latLng(north, east), // NE
                this.L.latLng(south, east), // SE
                this.L.latLng(south, west)  // SW
              ];
              // Crea il poligono rettangolare
              const polygon = this.L.polygon(points, { color: "#080807ff", weight: 5, opacity: 0.4 });
              this.featureGroup.addLayer(polygon);
        } else {
          setTimeout(() => this.drawableMap(), 200);
          console.warn('[drawableMap] Bounds non disponibili, retry...');
          return;
        }
        this.drawControl = new this.L.Control.Draw({
          draw: {         //nessuna forma disegnabile manualmente        
            polygon: false,
            polyline: false,
            circle: false,
            marker: false,
            circlemarker: false,
            rectangle: false
          },
          edit: {
            featureGroup: this.featureGroup
          }
        });
        this.map.addControl(this.drawControl);
        this.map.on('draw:edited', (e: any) => {
          e.layers.eachLayer((layer: any) => {
            MapLayerComponent.captureData[0] = layer.getBounds();
          });
        });
      });
    }
  }
  //funzione per caricare i dati nella mappa di pre-calcolo
  private loadCaptureData(mapDiv: HTMLElement | null): void {
    if(isPlatformBrowser(this.platformId) && this.map &&
      typeof this.map.fitBounds == 'function' && MapLayerComponent.captureData[0]) {
      setTimeout(() => {
        (this.map as any).fitBounds(MapLayerComponent.captureData[0]);
        setTimeout(() => {
          const minZoom = this.map.getMinZoom ? this.map.getMinZoom() : 1;
          const newZoom = Math.max(minZoom, this.map.getZoom() - 1);
          (this.map as any).setZoom(newZoom);
        }, 300);
      }, 100);
    } else {
      console.warn(`Elemento mappa con id '${this.mapId}' non trovato, dati non validi o 'fitBounds' non disponibile.`);
    }

    this.drawableMap();
  }

  private capturePolygon(): number[][] {
    const polygonCoords: number[][] = [];
    if (isPlatformBrowser(this.platformId) && this.map && this.featureGroup) {
      this.featureGroup.eachLayer((layer: any) => {
        if (layer instanceof this.L.Polygon) {
          const latLngs = layer.getLatLngs()[0]; // Ottieni i vertici del poligono
          latLngs.forEach((latLng: any) => {
            polygonCoords.push([latLng.lat, latLng.lng]);
          });
        }
      });
      if (polygonCoords.length === 0) {
        console.warn('Nessun poligono trovato nel featureGroup.');
      }
    } else {
      console.warn(`Elemento mappa con id '${this.mapId}' non trovato o 'featureGroup' non disponibile.`);
    }
    return polygonCoords;
  }
}