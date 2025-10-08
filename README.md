# Green Rating Algorithm

Green Rating Algorithm è un'applicazione web sviluppata in Angular che permette di selezionare, analizzare e visualizzare aree geografiche su mappa tramite Leaflet e OpenStreetMap. Il progetto integra:

- **Selezione interattiva di zone**: l'utente può disegnare e modificare poligoni (inizialmente rettangolari) direttamente sulla mappa.
- **Ricerca geografica**: tramite una search-bar integrata, è possibile cercare e localizzare indirizzi e luoghi sfruttando OSM Nominatim.
- **Editing geometrico avanzato**: la toolbar Leaflet Draw consente di modificare, spostare o eliminare la zona selezionata, con gestione automatica dei controlli.
- **Integrazione dati OSM**: la zona selezionata può essere usata per interrogare le API OSM e ottenere dati interni all'area.
- **Architettura modulare**: il codice è organizzato in componenti Angular, con servizi condivisi per la comunicazione tra le mappe e gestione degli eventi.


Questa repository è pensata per progetti di analisi ambientale, urbanistica, green rating e visualizzazione dati territoriali, con un'interfaccia moderna e responsive.

## Lato Server

- **Backend Python robusto**: gestione avanzata degli errori, conversione automatica da Overpass JSON a GeoJSON, fix per colonne mancanti e dati sporchi.
- **Gestione CRS**: tutti i GeoDataFrame ora hanno il CRS impostato e vengono riproiettati senza errori.
- **Fix colonne mancanti**: controllo e gestione delle colonne 'building', 'natural', ecc. per evitare crash con dati incompleti.
- **Endpoint multipli Overpass**: il server prova più endpoint Overpass e gestisce i timeout in modo automatico.
- **Supporto multiutente**: il backend Flask può essere avviato su tutte le interfacce (`0.0.0.0`) per permettere l'accesso da altri dispositivi in rete.
- **Conversione dati**: pipeline completa per passare da Overpass JSON a GeoDataFrame, con filtri robusti e compatibilità con gli algoritmi di rating.
- **Best practice .gitignore e requirements**: aggiornati per evitare il tracciamento di cache, file temporanei e dipendenze inutili.
- **Log errori e warning**: logging migliorato per distinguere tra errori bloccanti e warning di Overpass.
- **Ottimizzazione algoritmi**: tutti gli algoritmi ora gestiscono dati sporchi, CRS, colonne mancanti e conversioni senza crash.

Per dettagli tecnici sugli algoritmi o la struttura delle query, consulta i file Python nella cartella `Server/Algoritmi`.

---
# Greenratingalgorithm

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 20.2.0.

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Karma](https://karma-runner.github.io) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
