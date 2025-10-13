"""
    Algoritmo per il calcolo della conformità 3-30-300:
        Il programma esegue una catena di analisi per determinare quali edifici rispettano simultaneamente tre diverse regole di pianificazione urbana:
        1. Regola 3 (Linea di Vista): ogni edificio deve avere almeno 3 alberi visibili nel suo raggio d'azione.
        2. Regola 30 (Copertura Arborea): la percentuale di copertura arborea totale nella zona di studio deve superare una certa soglia.
        3. Regola 300 (Area Verde Vicina): ogni edificio deve trovarsi a una distanza massima di 300 metri da un'area verde pubblica.
        
        L'algoritmo esegue ciascuna di queste regole in modo indipendente e poi esegue una logica di "intersezione"
            per trovare gli edifici che soddisfano tutte le condizioni.
        
        MANCA:
            - una logica di salvataggio più robusta che non dia errori in caso di GeoDataFrame vuoti.
            - proiezione dei risultati in una heatmap.
            - selezione di un singolo edificio (da vedere una volta acquisito il frontend).
            - calcolo della media per edificio di soddisfazione della regola, e poi media delle medie per avere le proiezioni a colori sul piano generale;
"""

#importazioni
import geopandas as gpd
from osm2geojson import json2geojson
import logging

#importa le funzioni dagli script singoli
from .regola3 import run_rule_3
from .regola30 import run_rule_30
from .regola300 import run_rule_300

# nomi dei file di input e output
output_filename = "edifici_conformi_3_30_300.geojson"

"""
    Funzione principale che esegue l'analisi completa 3-30-300.
"""
def run_full_analysis(overpass_buildings, overpass_trees, overpass_green_areas):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("analizzatore_centrale")
    logger.info("Avvio dell'analisi completa 3-30-300...")

    #carica i dati una sola volta
    try:
        geojson_buildings = json2geojson(overpass_buildings)
        edifici = gpd.GeoDataFrame.from_features(geojson_buildings["features"])

        geojson_trees = json2geojson(overpass_trees)
        alberi = gpd.GeoDataFrame.from_features(geojson_trees["features"])

        geojson_green_areas = json2geojson(overpass_green_areas)
        aree_verdi = gpd.GeoDataFrame.from_features(geojson_green_areas["features"])

    except Exception as e:
        logger.error(f"Errore nel caricamento dei file: {e}")
        return

    logger.info(f"Numero totale di edifici nel dataset: {len(edifici)}")
    logger.info(f"Numero totale di alberi nel dataset: {len(alberi)}")
    logger.info(f"Numero totale di aree verdi nel dataset: {len(aree_verdi)}")

    #esegue gli algoritmi per ogni regola e ottieni i risultati
    logger.info("--- Esecuzione Regola 3 (Linea di Vista) ---")
    try:
        risultati_3 = run_rule_3(edifici, alberi)
        num_soddisfatti_3 = (risultati_3['visible_trees_count'] > 0).sum()
        logger.info(f"RISULTATO REGOLA 3: {num_soddisfatti_3} edifici soddisfano la regola (su {len(edifici)}).")
    except Exception as e:
        logger.error(f"Errore Regola 3: {e}")
        return

    logger.info("--- Esecuzione Regola 30 (Copertura Arborea) ---")
    try:
        percentage_30 = run_rule_30(edifici, alberi)
        logger.info(f"RISULTATO REGOLA 30: La copertura arborea è del {percentage_30:.2f}%.")
        if percentage_30 > 0.0:
            logger.info("La regola del 30% è soddisfatta a livello di zona.")
        else:
            logger.info("La regola del 30% NON è soddisfatta a livello di zona.")
    except Exception as e:
        logger.error(f"Errore Regola 30: {e}")
        return

    logger.info("--- Esecuzione Regola 300 (Area Verde Vicina) ---")
    try:
        risultati_300 = run_rule_300(edifici, aree_verdi)
        num_soddisfatti_300 = (risultati_300['score_300'] == 1).sum()
        logger.info(f"RISULTATO REGOLA 300: {num_soddisfatti_300} edifici soddisfano la regola (su {len(edifici)}).")
    except Exception as e:
        logger.error(f"Errore Regola 300: {e}")
        return

    logger.info("Intersezione dei risultati...")

    #filtro per la regola 3
    edifici_conformi_3 = risultati_3[risultati_3['visible_trees_count'] > 0]

    #filtro per la regola 300
    edifici_conformi_300 = risultati_300[risultati_300['score_300'] == 1]
    
    #intersezione dei GeoDataFrame
    edifici_intermedi = edifici_conformi_3.loc[edifici_conformi_3.index.intersection(edifici_conformi_300.index)].copy()

    logger.info(f"Edifici che soddisfano sia la Regola 3 che la Regola 300: {len(edifici_intermedi)}")

    #controllo della regola 30
    if percentage_30 > 0.0:
        logger.info("La regola 30 è soddisfatta, procedo con il salvataggio.")
        edifici_finali = edifici_intermedi.copy()
    else:
        logger.info("La regola 30 NON è soddisfatta, il risultato finale è 0.")
        #crea un GeoDataFrame vuoto in modo corretto
        edifici_finali = gpd.GeoDataFrame(columns=edifici.columns, crs=edifici.crs, geometry='geometry')

    #aggiungo le colonne di debug per l'output finale
    if not edifici_finali.empty:
        edifici_finali['visible_trees_count'] = risultati_3.loc[edifici_finali.index, 'visible_trees_count']
        edifici_finali['score_300'] = risultati_300.loc[edifici_finali.index, 'score_300']
        edifici_finali['coverage_percentage'] = percentage_30

    #salva il risultato finale
    if not edifici_finali.empty:
        logger.info(f"Analisi completata! Trovati {len(edifici_finali)} edifici che rispettano la regola 3-30-300.")
        logger.info(f"Risultato salvato in: {output_filename}")
        return edifici_finali.to_crs(edifici.crs)
        #.to_file(output_filename, driver='GeoJSON')
    else:
        logger.info("Nessun edificio trovato che rispetta tutte e 3 le regole.")

#main rule
if __name__ == "__main__":
    run_full_analysis()