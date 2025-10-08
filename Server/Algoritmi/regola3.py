"""
    Algoritmo per il calcolo della regola 3:
        il programma itera su ogni edificio passato come argomento, e gli alberi contenuti in un buffer che simula una distanza fattibile di visuale di una persona.
        Ogni albero ottenuto viene iterato a sua volta per l'edificio, controllando che esista un percorso 'visivo' tra i due elementi;
        viene quindi tracciato un segmento tra i due, e controllato se qualche altro oggetto (al momento gli altri edifici e basta) ostacolano la visuale.

        MANCA: - controllo altitudine;
               - scegliere un buffer di visuale con base scientifica;
               - decidere che elementi andare a prelevare da OSM per il controllo degli ostacoli.
"""

#importazioni
from shapely.geometry import LineString
import pandas as pd

"""
    Funzione che verifica se la linea di vista da un albero a un edificio è bloccata.
"""
def is_unobstructed(tree, building, all_buildings_gdf):         # TODO: modificare da edifici a elementi in generale
    try:
        #individuazione punto più vicino all'edificio per la linea di vista
        building_point = building.geometry.exterior.interpolate(building.geometry.exterior.project(tree.geometry))
        line_of_sight = LineString([tree.geometry, building_point])
    except Exception as e:
        return False
    
    #copia del GeoDataFrame e rimozione edificio corrente dalla lista
    other_buildings = all_buildings_gdf.loc[all_buildings_gdf.index != building.name]
    return not other_buildings.geometry.intersects(line_of_sight).any()

"""
    Funzione che calcola il numero di alberi visibili da ogni edificio
"""
def run_rule_3(edifici, alberi):

    #controllo input
    if edifici.empty or alberi.empty:
        print("Dati insufficienti per il calcolo. Assicurati che i GeoDataFrame non siano vuoti.")
        return edifici.assign(visible_trees_count=0)

    #proiezione edifici e gli alberi nel sistema di coordinate corretto
    #se non c'è il crs va messo
    if edifici.crs is None:
        edifici.set_crs("EPSG:4326", inplace=True)
    if alberi.crs is None:
        alberi.set_crs("EPSG:4326", inplace=True)
    if 'building' in edifici.columns:
        edifici_proj = edifici[edifici['building'].notna()].to_crs("EPSG:32632")
    else:
        edifici_proj = edifici.to_crs("EPSG:32632")
    if 'natural' in alberi.columns:
        alberi_proj = alberi[alberi['natural'].fillna('') == 'tree'].to_crs("EPSG:32632")
    else:
        alberi_proj = alberi.to_crs("EPSG:32632")

    #inizializza un GeoDataFrame per i risultati basato sugli edifici riproiettati
    risultato_edifici = edifici_proj.copy()
    risultato_edifici['visible_trees_count'] = 0

    print("Avvio del calcolo della linea di vista...")
    
    #itera su ogni edificio
    for idx, edificio in risultato_edifici.iterrows():
        #buffer di 300 metri
        view_buffer = edificio.geometry.buffer(300)
        
        #identifica gli alberi che si trovano all'interno del buffer
        nearby_trees = alberi_proj[alberi_proj.geometry.within(view_buffer)]

        #itera sugli alberi vicini e verifica la linea di vista
        visible_trees = 0
        for _, albero in nearby_trees.iterrows():
            if is_unobstructed(albero, edificio, edifici_proj):
                visible_trees += 1
                
        #aggiorna il conteggio per l'edificio corrente
        risultato_edifici.loc[idx, 'visible_trees_count'] = visible_trees

    #crea un GeoDataFrame finale e copia i risultati (indice e numero alberi visibili)
    final_result_df = pd.DataFrame(index=edifici.index)
    final_result_df['visible_trees_count'] = 0
    final_result_df.loc[risultato_edifici.index, 'visible_trees_count'] = risultato_edifici['visible_trees_count']
    
    #restituisce il risultato come GeoDataFrame
    final_result_gdf = edifici.copy()
    final_result_gdf = final_result_gdf.merge(final_result_df, left_index=True, right_index=True)
    return final_result_gdf

#Esempio di utilizzo singolo dell'algoritmo
"""edifici = gpd.read_file("./Edifici.geojson")
alberi = gpd.read_file("./Alberi.geojson")
print(run_rule_3(edifici, alberi))"""