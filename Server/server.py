# import
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
from osm2geojson import json2geojson
import geopandas as gpd
from Algoritmi.analizzatore_centrale import run_full_analysis
import logging
from shapely.geometry import Polygon


app = Flask(__name__)
# abilita CORS per permettere ad Angular (che è su un'altra porta) di chiamare l'API
CORS(app, resources={r"/api/*": {"origins": "*"}})

# configura il logging una sola volta per l'intera applicazione
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Endpoint per l'API
@app.route('/api/greenRatingAlgorithm', methods=['POST'])

# TODO: forse ha senso esporre le sotto funzioni per il calcolo di solo alcune regole?
# TODO: manca la heatMap: da aggiungere qui o nel client?
def greenRatingAlgorithm():

    try:
        # ricezione dei dati da client
        dati_ricevuti = request.get_json()
        polygon = dati_ricevuti.get('polygon')
        
        # query per Overpass API
        if(polygon):
            # aumento il poligono in base alla regola
            buffered_polygon_300 = increasePolygon(polygon, 300)
            buffered_polygon_3 = increasePolygon(polygon, 3)

            """
            concateno i punti del poligono in una stringa formattata per Overpass
            da client arrivano in formato json come lista di liste [[lat, lon], [lat, lon], ...]
            a overpass dobbiamo mandare "lat lon lat lon ..."
            """
            poly_str = " ".join([f"{lat} {lon}" for lat, lon in polygon])

            # controllo messo qui per fallback in caso di errore nel buffer con poly_str
            if not buffered_polygon_300 or not buffered_polygon_3:
                app.logger.warning(f"Impossibile creare il sovrapposizione per la regola 300 o 3. Uso il poligono di input.")
                buffered_polygon_300 = poly_str
                buffered_polygon_3 = poly_str
                # TODO: eliminare questo errore se funziona
                # ritorno di errore per prova funziona
                return jsonify({'errore': 'Impossibile creare il buffer per la query Overpass'}), 500

            # costruisco le query e le eseguo
            buildings_query = build_query(0, poly_str)
            edifici = overpass_query(buildings_query)
            if edifici is None:
                return jsonify({'errore': 'Nessun edificio selezionato'}), 504
            trees_query = build_query(1, buffered_polygon_3)
            alberi = overpass_query(trees_query)
            green_areas_query = build_query(2, buffered_polygon_300)
            aree_verdi = overpass_query(green_areas_query)
        else:
            # http 400 bad request
            return jsonify({'errore': 'Dati geometrici mancanti o non validi'}), 400

        # conversione dei dati da OSM a GeoDataFrame
        try:
            geojson_buildings = json2geojson(edifici)
            edifici = gpd.GeoDataFrame.from_features(geojson_buildings["features"])

            """ Garantisce che la colonna di geometria sia impostata correttamente
            e che il CRS sia presente, anche se GeoPandas ha fallito nel farlo
            con from_features. """
            if not edifici.empty:
                if edifici.geometry.name != 'geometry':
                    edifici = edifici.set_geometry('geometry')
                if edifici.crs is None:
                    edifici = edifici.set_crs('EPSG:4326', allow_override=True)

            #solo gli edifici devono non essere nulli, gli altri possono essere vuoti
            #pertanto dobbiamo gestire la conversione in json di elementi Nulli
            if(alberi is None):
                alberi = gpd.GeoDataFrame(crs="EPSG:4326") # GeoDataFrame vuoto
            else:
                geojson_trees = json2geojson(alberi)
                alberi = gpd.GeoDataFrame.from_features(geojson_trees["features"], crs="EPSG:4326")

            if(aree_verdi is None):
                aree_verdi = gpd.GeoDataFrame(crs="EPSG:4326") # GeoDataFrame vuoto
            else:
                geojson_green_areas = json2geojson(aree_verdi)
                aree_verdi = gpd.GeoDataFrame.from_features(geojson_green_areas["features"], crs="EPSG:4326")

        except Exception as e:
            return jsonify({'errore': f'Errore nella conversione in GeoDataFrame dei dati OSM: {e}'}), 500

        # esecuzione degli algoritmi
        result = run_full_analysis(edifici, alberi, aree_verdi)

        # definiamo un GeoJSON vuoto standard da usare come fallback
        empty_geojson_fallback = '{"type": "FeatureCollection", "features": []}'

        # preparazione della risposta in formato GeoJSON (con gestione accurata dei casi particolari)
        edifici_geojson = edifici.to_json() if not edifici.empty else empty_geojson_fallback
        alberi_geojson = alberi.to_json() if not alberi.empty else empty_geojson_fallback
        aree_verdi_geojson = aree_verdi.to_json() if not aree_verdi.empty else empty_geojson_fallback

        if result is None or result.empty:
             risultati_geojson = '{"type": "FeatureCollection", "features": []}'
        elif not hasattr(result, 'to_json'):
             # Se non è GeoDataFrame, converti a stringa di errore (improbabile, ma sicuro)
             app.logger.error("Il risultato non è un oggetto serializzabile!")
             risultati_geojson = '{"type": "FeatureCollection", "features": []}'
        else:
             # Serializzazione del GeoDataFrame (Se fallisce qui, il problema è nel GDF stesso)
             risultati_geojson = result.to_json()

        risultato = {
            'messaggio': 'Analisi completata con successo.',
            'edifici': edifici_geojson,
            'alberi': alberi_geojson,
            'aree_verdi': aree_verdi_geojson,
            'risultati': risultati_geojson
        }

        return jsonify(risultato), 200

    except Exception as e:
        # logga l'errore completo per il debug lato server
        app.logger.error(f"Errore durante l'elaborazione: {e}")
        # invia un messaggio di errore generico ad Angular
        return jsonify({'errore': f'Errore del server: {str(e)}'}), 500


# funzione per costruire la query a Overpass API in base al tipo di dato richiesto
"""
la libreria python OSMnx è molto utile per lavorare con dati OSM, in particolare per un'analisi e visualizzazione avanzata,
ossia quello che abbiamo fatto con geopandas negli algoritmi. Come database da cui solo estrapolare i dati OSM,
Overpass API è più efficiente e veloce. Oltre a ciò, dava anche problemi di timeout e incompatibilità.
"""
def build_query(type, poly_str):

    # type 0 = edifici, type 1 = alberi, type 2 = aree verdi
    if type == 0:
        query = f"""
            [out:json][timeout:25];
            (
            way["building"](poly:"{poly_str}");
            relation["building"](poly:"{poly_str}");
            );
            out body;
            >;
            out skel qt;
        """
    elif type == 1:
        query = f"""
            [out:json][timeout:25];
            (
            node["natural"="tree"](poly:"{poly_str}");
            node["natural"="tree_row"](poly:"{poly_str}");
            way["natural"="tree"](poly:"{poly_str}");
            );
            out body;
            >;
            out skel qt;
        """
    elif type == 2:
        query = f"""
            [out:json][timeout:25];
            (
            way["leisure"="park"](poly:"{poly_str}");
            way["leisure"="garden"](poly:"{poly_str}");
            way["landuse"="grass"](poly:"{poly_str}");
            way["landuse"="forest"](poly:"{poly_str}");
            way["natural"="wood"](poly:"{poly_str}");
            );
            out body;
            >;
            out skel qt;
        """
    else:
        query = ""
    return query
    

def overpass_query(query):

    # lista di endpoint alternativi per la richiesta (spesso sovvraccaricati)
    overpass_endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter"
    ]
    import time
    for url in overpass_endpoints:
        try:
            response = requests.post(url, query, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result
        except requests.exceptions.Timeout:
            print(f"Timeout su {url}, provo il prossimo endpoint...")
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"Warning: il seguente server è sovvraccarico o ha generato un errore ---> {url}: {e}")
            time.sleep(2)
    return None

# funzione per aumentare la dimensione del calcolo di una certa distanza, per comprendere gli elementi che rientrano nelle distanze ma non nel poligono
def increasePolygon(polygon, rule):
    try:
        # Shapely Polygon vuole coordinate [(lon, lat)], quindi invertite rispetto a prima (simile a Leaflet)
        poly_coords = [(lon, lat) for lat, lon in polygon]
        
        # crea un GeoDataFrame con il poligono di input
        gdf_input = gpd.GeoDataFrame(
            [{'geometry': Polygon(poly_coords)}], 
            crs="EPSG:4326"
        )

        # TODO: definire meglio la visuale di una persona rispetto ad un albero per il calcolo della regola 3!!!
        # definisco la dimensione del buffer in metri in base alla regola
        if rule == 300:
            bufferSize = 300  # buffer di 300 metri
        elif rule == 3:
            bufferSize = 50    # buffer di 50 metri
        
        # proietto in CRS metrico (UTM 32N), calcola buffer, riproietta in lat/lon
        gdf_proj = gdf_input.to_crs("EPSG:32632")
        gdf_proj_buffered = gdf_proj.buffer(bufferSize)
        gdf_buffered_unproj = gdf_proj_buffered.to_crs("EPSG:4326")

        # estraggo le coordinate (lon, lat) dal poligono bufferizzato
        buffered_poly_geom = gdf_buffered_unproj.geometry.iloc[0]
        
        # converto in stringa "lat lon..." per Overpass
        return " ".join([f"{lat} {lon}" for lon, lat in buffered_poly_geom.exterior.coords])

    except Exception as e:
        app.logger.warning(f"Impossibile creare il sovvra-Buffer per la regola 300 o 3: {e}. Uso il poligono di input.")
        # Fallback: usa il poligono originale se il buffer fallisce
        return None

if __name__ == '__main__':
    # Esegue il server solo su localhost per sicurezza durante lo sviluppo.
    #app.run(host='127.0.0.1', port=5000, debug=True)
    # Esegue il server su tutte le interfacce, così anche altri utenti possono collegarsi
    # app.run(host='0.0.0.0', port=5000, debug=True)
    pass