# import
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
from Algoritmi.analizzatore_centrale import run_full_analysis
# Non serve modificare sys.path se "algoritmi" è nella stessa cartella


app = Flask(__name__)
# abilita CORS per permettere ad Angular (che è su un'altra porta) di chiamare l'API
CORS(app, resources={r"/*": {"origins": "*"}})

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
            """
            concateno i punti del poligono in una stringa formattata per Overpass
            da client arrivano in formato json come lista di liste [[lat, lon], [lat, lon], ...]
            a overpass dobbiamo mandare "lat lon lat lon ..."
            """
            poly_str = " ".join([f"{lat} {lon}" for lat, lon in polygon])

            # costruisco le query e le eseguo
            buildings_query = build_query(0, poly_str)
            edifici = overpass_query(buildings_query)
            if edifici is None:
                return jsonify({'errore': 'Tutti gli endpoint Overpass hanno fallito o sono in timeout'}), 504
            trees_query = build_query(1, poly_str)
            alberi = overpass_query(trees_query)
            green_areas_query = build_query(2, poly_str)
            aree_verdi = overpass_query(green_areas_query)
        else:
            # http 400 bad request
            return jsonify({'errore': 'Dati geometrici mancanti o non validi'}), 400


        # esecuzione degli algoritmi
        result = run_full_analysis(edifici, alberi, aree_verdi)
        edifici_geojson = edifici.to_json()
        alberi_geojson = alberi.to_json()
        aree_verdi_geojson = aree_verdi.to_json()
        if result is not None and hasattr(result, 'to_json'):
            risultati_geojson = result.to_json()
        else:
            risultati_geojson = '{"type": "FeatureCollection", "features": []}'

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
    return jsonify({'errore': 'Tutti gli endpoint Overpass hanno fallito o sono in timeout'}), 504

if __name__ == '__main__':
    # Esegue il server solo su localhost per sicurezza durante lo sviluppo.
    #app.run(host='127.0.0.1', port=5000, debug=True)
    # Esegue il server su tutte le interfacce, così anche altri utenti possono collegarsi
    # app.run(host='0.0.0.0', port=5000, debug=True)
    pass