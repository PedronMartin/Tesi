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
    Algoritmo per il calcolo della Regola 30:
        Il programma calcola la percentuale di copertura arborea totale su una data area di studio.
        Questa percentuale non è un valore per singolo edificio, ma un indicatore di conformità a livello di zona che viene applicato a tutti gli edifici nel dataset.
        Il calcolo si basa su due fasi principali:
            1. Definizione dell'area di studio: l'area totale viene calcolata dal poligono generato dall'utente nel frontend, in metri quadrati.
            2. Calcolo dell'area arborea: viene creato un buffer di 2 metri intorno a ogni albero per stimarne l'area di copertura.
                Tutti questi buffer vengono poi uniti in un unico poligono per calcolare l'area totale coperta dagli alberi.

        MANCA:
            1- L'area di studio deve essere definita in modo più rigoroso, ad esempio utilizzando il confine del quartiere o della città,
                    invece di basarsi solo sugli elementi del dataset.
            2- La regola andrebbe adattata al dataset della tesi di Enrico, usando il suo sistema di classificazione delle geometrie degli alberi.

        NOTE:
            1- la Regola 30 parla di 'Copertura Arborea'.
                Per stimarla con i dati OSM, devo usare un'interpretazione pura (solo alberi, foreste, boschi)
                    oppure un'interpretazione più ampia (includendo parchi e prati); in questo momento usiamo sia alberi
                    che prati/giardini pubblici, anche se nella definizione originale della regola si parla
                    esclusivamente di copertura '''arborea'...quindi? (CHIEDERE A PROFESSORE)
            2- per il calcolo dell'area coperta dagli alberi puntiformi, al momento stiamo usando un buffer di 2 metri.
                Questo valore potrebbe essere raffinato in base a dati più specifici sugli alberi o medie prese da qualche studio scientifico
                magari prediligendo la tipologia di albero più comune per un contesto urbano e nelle città popolate.
"""

#importazioni
import geopandas as gpd
from shapely.ops import unary_union
import pandas as pd
import logging
import numpy as np

#logger globale
logger = logging.getLogger("regola30")
logger.addHandler(logging.NullHandler())

#costante che rappresenta il raggio in metri da considerare per ogni albero puntiforme
TREE_RADIUS = 2  # metri

"""
    Funzione che calcola la percentuale di copertura arborea per una data area.
"""
def run_rule_30(edifici, alberi, polygon_gdf):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("regola30")

    #controllo input
    if edifici.empty or alberi.empty or polygon_gdf.empty:
        logger.warning("Dati insufficienti per il calcolo. Assicurati che i GeoDataFrame non siano vuoti.")
        return 0.0

    try:
        #proiezione in sistema metrico degli input
        edifici_proj = edifici.to_crs("EPSG:32632")
        alberi_proj = alberi.to_crs("EPSG:32632")
        polygon_proj = polygon_gdf.to_crs("EPSG:32632")

        """
        #calcolo dell'area totale coperta dagli alberi
        alberi_buffer = alberi_proj.buffer(2)
        trees_total_area = unary_union(alberi_buffer.geometry).area"""

        #calcolo dell'area totale della zona di studio
        area_totale = polygon_proj.geometry.area.sum()
        if area_totale == 0:
            logger.warning("L'area totale della zona di studio è 0.")
            return 0.0

        #calcolo dell'area totale coperta dagli alberi
        trees_total_area = calculate_trees_area(alberi_proj, polygon_proj)

        #calcolo dell'area totale di foreste e boschi


        #calcola e controllo del risultato
        percentage = (trees_total_area / area_totale) * 100
        if percentage > 100:
            percentage = 100.0

    except Exception as e:
        logger.error(f"Errore nel calcolo della copertura arborea: {e}")
        return 0.0

    return percentage

#Esempio di utilizzo singolo dell'algoritmo
"""edifici = gpd.read_file("./INPUT/Edifici.geojson")
alberi = gpd.read_file("./INPUT/Alberi.geojson")
print(run_rule_30(edifici, alberi))"""

"""
    Funzione ausiliaria per calcolare l'area totale coperta dagli alberi interni al poligono di studio.
    Esegue un ritaglio dei dati degli alberi in base alla tipologia di appartenenza geometrica:
        gli alberi, considerati punti inizialmente, vengono considerati anche se sono parzialmente all'interno del poligono di studio;
        i poligoni (boschi, foreste) vengono considerati rispetto all'effettiva loro parte che ricade all'interno del poligono di studio (clip).
    Restituisce l'area totale coperta dagli alberi (in metri quadrati).
"""
def calculate_trees_area(alberi, area):

    try:

        #ritaglia i GDF degli alberi; i punti sono automaticamente inclusi, mentre i poligoni vengono ritagliati
        alberi_in_area = gpd.clip(alberi, area)

        #gestione e calcolo poligoni (boschi, foreste) ---
        alberi_polygons = alberi_in_area[alberi_in_area.geom_type.isin(['Polygon', 'MultiPolygon'])]
        area_from_polygons = alberi_polygons.geometry.area.sum()

        #estraggo alberi contrassegnati come punti
        alberi_points = alberi[alberi.geom_type == 'Point']
        
        #se non ci sono alberi puntiformi, ritorno l'area calcolata dai poligoni
        if alberi_points.empty:
            logger.info("Nessun albero puntiforme trovato nel dataset.")
            return area_from_polygons

        #seleziono solo gli alberi puntiformi dentro l'area di studio
        alberi_points_in_area = alberi_points[
            alberi_points.geometry.within(area.unary_union)
        ]
        
        area_from_points = 0.0
        if not alberi_points_in_area.empty:
            #calcolo l'area di un singolo cerchio (pi * r^2)
            area_per_tree = np.pi * (TREE_RADIUS * TREE_RADIUS)
            #moltiplico per il numero di alberi
            area_from_points = len(alberi_points_in_area) * area_per_tree
            
        #ritorno finale prodotto dalla somma dell'area coperta dagli alberi puntiformi e quelli poligonali
        return area_from_polygons + area_from_points

    except Exception as e:
        logger.error(f"Errore nel calcolo del numeratore (area arborea): {e}")
        return 0.0