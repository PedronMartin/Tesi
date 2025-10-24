import { Component, PLATFORM_ID, Inject, Input } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-map-result',
  imports: [],
  templateUrl: './map-result.html',
  styleUrl: './map-result.css'
})
export class MapResult {

  //campi
  private L: any;
  private map: any;
  private edifici: any[] = [];
  private alberi: any[] = [];
  private aree_verdi: any[] = [];
  private result: any[] = [];
  private resultsLayer: any;
  @Input() dati: any;
  @Input() polygon: number[][] = [];

  //costruttore
  constructor(@Inject(PLATFORM_ID) private platformId: Object) { }

  //appena caricato il layer della mappa, andiamo a inizializzarla con i dati ricevuti
  ngAfterViewInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      import('leaflet').then(L => {
        let mapDiv: HTMLElement | null = document.getElementById("map");
        if (!mapDiv) {
          console.error("Impossibile trovare il div della mappa con id 'map'");
          return;
        }
        this.L = L;

        // --- FIX: Distruggi la mappa se esiste già ---
        // Previene errori se il componente viene ricaricato (es. Hot-Reload)
        if (this.map) {
          this.map.remove();
          this.map = null;
        }

        // --- FIX: Logica Bounds e Fallback migliorata ---
        let bounds: any;
        
        // Controlla se il poligono esiste E ha almeno un punto
        if (this.polygon && this.polygon.length > 0) {
          const latlngs = this.polygon.map((coord: number[]) => L.latLng(coord[0], coord[1]));
          bounds = L.latLngBounds(latlngs);
        } else {
          // fallback: centro Italia (Roma)
          const fallbackCenter = L.latLng(41.9028, 12.4964);
          // Creiamo un "bounds" fittizio per il fallback zoomando sul centro
          bounds = fallbackCenter.toBounds(100000); // 100km di raggio
        }

        // 1. CREA LA MAPPA
        // Inizializza la mappa sul div
        this.map = L.map('map');

        // 2. AGGIUNGI I TILES (LO SFONDO DELLA MAPPA)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 30
        }).addTo(this.map);

        // 3. CENTRA E ZOOMA LA MAPPA
        // fitBounds calcola automaticamente centro e zoom
        this.map.fitBounds(bounds);
        this.map.setZoom(this.map.getZoom() - 1); // Zoom out di 1 livello per migliore visuale

        this.loadData();
      });
    }
  }

  private loadData(){
    if (!this.dati || !this.map || !this.L) {
      console.error("Dati non validi o mappa non inizializzata");
      return;
    }
    //funzione per estrapolare i vari dati
    this.extractData();

    //carico i risultati sulla mappa
    try {

      //gestione caso vuoto: nessun edificio ha soddisfatto le regole
      if (!this.result || this.result.length === 0) {
        console.log("Nessun edificio risultato da visualizzare (GeoJSON vuoto).");
        return;
      }

      /* disegno i risultati sulla mappa
      // L.geoJSON è la funzione che fa tutto:
      // 1. Legge l'oggetto GeoJSON
      // 2. Inverte automaticamente [lon, lat] in (lat, lon) per Leaflet
      // 3. Disegna i poligoni degli edifici */
      this.resultsLayer = this.L.geoJSON(this.result, {

        //aggiungiamo uno stile ai poligoni risultati
        style: (feature: any) => {
          return {
            color: "#00FF00", // Verde acceso
            weight: 2,
            opacity: 1,
            fillOpacity: 0.3
          };
        },

        //aggiungiamo un popup a ogni edificio
        onEachFeature: (feature: any, layer: any) => {
          if (feature.properties) {
            const props = feature.properties;
            //creiamo un popup con i dati delle regole
            let popupContent = `<b>Edificio ID: ${props.id}</b><br>`;
            if(props.name) popupContent += `Nome: ${props.name}<br>`;
            popupContent += `Alberi visibili: ${props.visible_trees_count}<br>`;
            popupContent += `Score 300m: ${props.score_300 === 1 ? 'Sì' : 'No'}<br>`;
            popupContent += `Copertura Zona: ${props.coverage_percentage.toFixed(2)}%`;
            
            layer.bindPopup(popupContent);
          }
        }

      }).addTo(this.map);

    } catch (e) {
      console.error("Errore fatale nel parsing o disegno del GeoJSON 'risultati':", e);
      console.error("Dati ricevuti (stringa):", this.dati['risultati']);
    }

    const colors = ['#FF0000', '#ffee05ff', '#1626b8ff'];
    const labels = ['Edifici', 'Alberi', 'Aree Verdi'];
    for (let i = 0; i < 3; i++) {
      this.otherLoading(colors[i], labels[i]);
    }
  }

  //estrapolazione dati
  private extractData(){
    this.edifici = JSON.parse(this.dati['edifici']);
    this.alberi = JSON.parse(this.dati['alberi']);
    this.aree_verdi = JSON.parse(this.dati['aree_verdi']);
    this.result = JSON.parse(this.dati['risultati']);
    console.log("Risultati: ", this.result);
  }

  //funzione provvisoria per la visualizzazione dei dati di calcolo
  private otherLoading(color: string, label: string){
    /*

    let Input;
    switch(label){
      case 'Edifici': Input = this.edifici;
                      break;
      case 'Alberi': Input = this.alberi;
                     break;
      case 'Aree Verdi': Input = this.aree_verdi;
                        break;
    }

    //gestione caso vuoto: nessun edificio ha soddisfatto le regole
    if(!Input || Input.length === 0) {
        console.log("Nessun dato input da visualizzare (GeoJSON vuoto).");
        return;
    }
*/
      /* disegno i risultati sulla mappa
      // L.geoJSON è la funzione che fa tutto:
      // 1. Legge l'oggetto GeoJSON
      // 2. Inverte automaticamente [lon, lat] in (lat, lon) per Leaflet
      // 3. Disegna i poligoni degli edifici *//*
      this.L.geoJSON(Input, {

        //aggiungiamo uno stile ai poligoni risultati
        style: (feature: any) => {
          return {
            color: color, // Verde acceso
            weight: 2,
            opacity: 1,
            fillOpacity: 0.3
          };
        },
      }).addTo(this.map);*/
  }
}
