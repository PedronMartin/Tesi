# Copyright 2026 [Martin Pedron Giuseppe]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Script per la gestione dei grafi stradali delle città.
Fornisce funzionalità per:
- caricamento e caching dei grafi stradali da file GraphML;
- rilevamento della città in base al poligono di input arrivato dal frontend;
La funzione principale è lo spatial join, in modalità "intersects", per determinare se il poligono utente interseca la figura di una città in almeno un punto.
La versione "within" non è adatta perché richiede che il poligono utente sia completamente contenuto all'interno del confine della città.
Ci penserà poi Rule300 a gestire i casi in cui un area verde è fuori dal grafo cittadino.
"""

import os
import geopandas as gpd
import osmnx as ox
from shapely.geometry import shape

#configurazione percorsi relativi
file_boundaries = "./Data/city_boundaries.json"
GRAPHS_DIR = "./Data/Grafi_stradali"

class graphsManager:
    _instance = None
    
    #singleton pattern
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(graphsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    """
    Se mai inizializzato, carica i confini delle città da file. Altrimenti usa quelli in memoria.
    """
    def __init__(self):
        if self._initialized:
            return
        
        self._cities_boundaries = self._load_boundaries()
        self._loaded_graphs = {}    #cache grafi in RAM
        self._initialized = True

    """
    Carica i confini delle città da file, se disponibile. Altrimenti ritorna GDF vuoto.
    """
    def _load_boundaries(self):

        #file non presente
        if not os.path.exists(file_boundaries):
            print(f"File confini città non trovato in '{file_boundaries}'")
            return gpd.GeoDataFrame()
        
        #carica file in GDF
        try:
            gdf = gpd.read_file(file_boundaries)
            print(f"Confini caricati: {len(gdf)} città disponibili.")
            return gdf
        except Exception as e:
            print(f"Errore caricamento confini città: {e}")
            return gpd.GeoDataFrame()


    """
    Determina se il poligono dell'utente ricade in una delle città gestite.
    @param input_polygon_shapely: poligono shapely dell'area utente creato in server.py (viene anche usato per il buffer sulle richieste Overpass)
    @return: nome della città se trovata, altrimenti None. In pratica dice SI/NO, se si, quale città.
    """
    def get_city_from_polygon(self, input_polygon_shapely):

        #se non ho confini caricati, esco subito
        if self._cities_boundaries.empty:
            return None

        try:
            #creo gdf temporaneo
            tmp = gpd.GeoDataFrame({'geometry': [input_polygon_shapely]}, crs="EPSG:4326")
            
            #spatial join per verificare intersezione con confini città
            joined = gpd.sjoin(tmp, self._cities_boundaries, how="inner", predicate="intersects")
            
            if not joined.empty:
                city_name = joined.iloc[0]['city_name']
                print(f"Match trovato: città di {city_name}")
                return city_name
            
            return None
            
        except Exception as e:
            print(f"Errore intersezione poligono input con confini città: {e}")
            return None

    """
    Restituisce il grafo della città richiesta, caricandolo da disco se non già in RAM.
    @param city_name: nome della città di cui si vuole il grafo
    @return: grafo osmnx della città, o None se non trovato
    """
    def get_graph(self, city_name):
        #se già caricata, la ritorno
        if city_name in self._loaded_graphs:
            return self._loaded_graphs[city_name]

        #costruisco percorso relativo per file specifico graphml
        safe_name = city_name.replace(" ", "_").replace(",", "")
        file_path = os.path.join(GRAPHS_DIR, f"{safe_name}.graphml")

        if not os.path.exists(file_path):
            print(f"Grafo non trovato: {file_path}")
            return None

        #carico da disco
        print(f"Caricamento grafo {city_name} da disco.")
        try:
            G = ox.load_graphml(file_path)
            
            #proietto subito in metri per calcoli corretti
            G_proj = ox.project_graph(G)
            
            #mi salvo che è stata caricata
            self._loaded_graphs[city_name] = G_proj
            print(f"Grafo {city_name} caricato correttamente.")
            
            return G_proj
            
        except Exception as e:
            print(f"Errore caricamento grafo: {e}")
            return None

#istanza globale
graphs_manager = graphsManager()