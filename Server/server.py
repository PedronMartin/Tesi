# import
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from Algoritmi.analizzatore_centrale import run_full_analysis
# Non serve modificare sys.path se "algoritmi" è nella stessa cartella


app = Flask(__name__)
# abilita CORS per permettere ad Angular (che è su un'altra porta) di chiamare l'API
CORS(app) 

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
        data = overpass_query(polygon)

        print(data)
        # esecuzione degli algoritmi
        result = run_full_analysis()

        # TODO: calcolo rating (?)
        print(result)

        # impacchettamento risposta
        risultato = {
            'messaggio': 'Analisi completata con successo.',
            'input_polygon': polygon,
            'metriche': {"""
                'edifici_trovati': result.get('edifici_trovati', 0),
                'punteggio_finale_3_30_300': round(result.get('punteggio_finale_3_30_300', 0), 2),"""
            }
        }
        
        # ritorno al client
        return jsonify(risultato), 200

    except Exception as e:
        # logga l'errore completo per il debug lato server
        app.logger.error(f"Errore durante l'elaborazione: {e}")
        # invia un messaggio di errore generico ad Angular
        return jsonify({'errore': f'Errore del server: {str(e)}'}), 500


# funzione per eseguire la query a Overpass API
"""
la libreria python OSMnx è molto utile per lavorare con dati OSM, in particolare per un'analisi e visualizzazione avanzata,
ossia quello che abbiamo fatto con geopandas negli algoritmi. Come database da cui solo estrapolare i dati OSM,
Overpass API è più efficiente e veloce. Oltre a ciò, dava anche problemi di timeout e incompatibilità.
"""
def overpass_query(polygon):

    if polygon:
        """
        concateno i punti del poligono in una stringa formattata per Overpass
        da client arrivano in formato json come lista di liste [[lat, lon], [lat, lon], ...]
        a overpass dobbiamo mandare "lat lon lat lon ..."
        """
        poly_str = " ".join([f"{lat} {lon}" for lat, lon in polygon])
        query = f"""
            [out:json][timeout:25];
            (
            way["building"](poly:"{poly_str}");
            relation["building"](poly:"{poly_str}");
            way["leisure"="park"](poly:"{poly_str}");
            way["leisure"="garden"](poly:"{poly_str}");
            way["landuse"="grass"](poly:"{poly_str}");
            way["landuse"="forest"](poly:"{poly_str}");
            way["natural"="tree"](poly:"{poly_str}");
            way["natural"="wood"](poly:"{poly_str}");
            node["natural"="tree"](poly:"{poly_str}");
            node["natural"="tree_row"](poly:"{poly_str}");
            );
            out body;
            >;
            out skel qt;
        """
    else:
        # http 400 bad request
        return jsonify({'errore': 'Dati geometrici mancanti o non validi'}), 400
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    response = requests.post(overpass_url, query)                   # se non va mettere data=query
    response.raise_for_status()                                     # solleva un'eccezione per errori HTTP
    result = response.json()                                        # dati OSM in formato JSON
    return result

if __name__ == '__main__':
    # Esegue il server solo su localhost per sicurezza durante lo sviluppo.
    app.run(host='127.0.0.1', port=5000, debug=True)