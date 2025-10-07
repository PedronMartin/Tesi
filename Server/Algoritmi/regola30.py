"""
    Algoritmo per il calcolo della Regola 30:
        Il programma calcola la percentuale di copertura arborea totale su una data area di studio.
        Questa percentuale non è un valore per singolo edificio, ma un indicatore di conformità a livello di zona che viene applicato a tutti gli edifici nel dataset.
        Il calcolo si basa su due fasi principali:
            1. Definizione dell'area di studio: l'area totale viene calcolata unendo i poligoni di tutti gli edifici e gli alberi presenti nel dataset.
                Questo crea un'unica geometria che racchiude tutti gli elementi di interesse.
            2. Calcolo dell'area arborea: viene creato un buffer di 2 metri intorno a ogni albero per stimarne l'area di copertura.
                Tutti questi buffer vengono poi uniti in un unico poligono per calcolare l'area totale coperta dagli alberi.

        MANCA: - L'area di studio deve essere definita in modo più rigoroso, ad esempio utilizzando il confine del quartiere o della città,
                    invece di basarsi solo sugli elementi del dataset.
            - La regola andrebbe adattata al dataset della tesi di Enrico, usando il suo sistema di classificazione delle geometrie degli alberi.
"""

#importazioni
import geopandas as gpd
from shapely.ops import unary_union
import pandas as pd

"""
    Funzione che calcola la percentuale di copertura arborea per una data area.
"""
def run_rule_30(edifici, alberi):           #probabilmente va aggiunto qualcosa riguardante le geometrie della zona, magari i punti di confine che creano una geometria

    #controllo input
    if edifici.empty or alberi.empty:
        print("Dati insufficienti per il calcolo. Assicurati che i GeoDataFrame non siano vuoti.")
        return 0.0

    #proiezione edifici e gli alberi nel sistema di coordinate corretto
    edifici_proj = edifici.to_crs("EPSG:32632")
    alberi_proj = alberi.to_crs("EPSG:32632")

    #calcolo dell'area totale coperta dagli alberi
    #crea un buffer di 2 metri attorno a ogni albero
    alberi_buffer = alberi_proj.buffer(2)
    #unisce i buffer e calcola l'area totale
    trees_total_area = unary_union(alberi_buffer.geometry).area

    #calcolo dell'area totale della zona di studio
    #unisce gli edifici e gli alberi in un unico GeoDataFrame per definire l'area di studio
    combined_geometries = pd.concat([edifici_proj, alberi_proj], ignore_index=True)

    #unisce le geometrie per formare un unico poligono e calcolarne l'area
    study_area_geometry = unary_union(combined_geometries.geometry)
    study_area = study_area_geometry.area

    #calcola la percentuale di copertura
    percentage = (trees_total_area / study_area) * 100
    
    return percentage

#Esempio di utilizzo singolo dell'algoritmo
"""edifici = gpd.read_file("./INPUT/Edifici.geojson")
alberi = gpd.read_file("./INPUT/Alberi.geojson")
print(run_rule_30(edifici, alberi))"""