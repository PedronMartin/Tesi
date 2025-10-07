"""
    Algoritmo per il calcolo della Regola 300:
        Il programma verifica, per ogni edificio, se è presente un'area verde pubblica nel raggio di 300 metri.
        Il calcolo si basa su una "unione spaziale" tra gli edifici e le aree verdi.
            1. Creazione del buffer: per ogni edificio, viene creato un'area di 300 metri (un "buffer"). Questo buffer rappresenta la zona di ricerca.
            2. Unione spaziale (Spatial Join): i buffer degli edifici vengono uniti alle geometrie delle aree verdi.
                Un edificio supera il test se il suo buffer interseca almeno un'area verde.
            3. Attribuzione del punteggio: ogni edificio che interseca un'area verde riceve un punteggio di 1, mentre gli altri ricevono 0.

        MANCA:
            - La regola andrebbe perfezionata per distinguere la tipologia di area verde (ad esempio, un grande parco rispetto a una piccola aiuola).
            - Il calcolo non tiene conto della disponibilità dell'area verde (ad esempio, se è recintata o accessibile al pubblico).
            - bisogna controllare se il buffer di 300 metri parte dal centro dell'edificio oppure dal perimetro (che sarebbe la versione desiderata).
            - forse bisogna aggiungere già qui il calcolo del percorso per non sovvraccaricare il frontend con Leaflet;
            - decidere se contare proprio il numero di aree verdi (e dare più peso alla regola) oppure come fatto fermare la ricerca una volta che se ne trova uno.
"""

# importazioni
import geopandas as gpd
import pandas as pd

"""
    Funzione che verifica la presenza di aree verdi entro 300 metri da ogni edificio.
"""
def run_rule_300(edifici, aree_verdi):

    #controllo input
    if edifici.empty or aree_verdi.empty:
        print("Dati insufficienti per il calcolo. Assicurati che i GeoDataFrame non siano vuoti.")
        return edifici.assign(score_300=0)

    #proiezione edifici e aree verdi nel sistema di coordinate corretto (metri)
    edifici_proj = edifici.to_crs("EPSG:32632")
    aree_verdi_proj = aree_verdi.to_crs("EPSG:32632")

    #crea una copia degli edifici per il buffer e aggiunge una colonna per l'indice originale
    edifici_buffer = edifici_proj.copy()
    edifici_buffer['geometry'] = edifici_buffer.geometry.buffer(300)
    edifici_buffer['original_index'] = edifici_buffer.index

    #esegue una unione spaziale (spatial join) per trovare gli edifici con aree verdi vicine
    #how="inner" garantisce che vengano considerate solo le intersezioni
    join_result = gpd.sjoin(edifici_buffer, aree_verdi_proj, how="inner", predicate='intersects')

    #inizializza il GeoDataFrame finale con la colonna del punteggio
    risultato_finale = edifici.copy()
    risultato_finale['score_300'] = 0
    
    #aggiorna il punteggio solo per gli edifici che hanno superato il test
    if not join_result.empty:
        #ottiene gli indici univoci degli edifici che intersecano un'area verde
        soddisfatti_index = join_result['original_index'].unique()
        #assegna il punteggio di 1 a questi edifici
        risultato_finale.loc[soddisfatti_index, 'score_300'] = 1

    return risultato_finale

#Esempio di utilizzo singolo dell'algoritmo
"""edifici = gpd.read_file("./INPUT/Edifici.geojson")
areeverdi = gpd.read_file("./INPUT/Areeverdi.geojson")
print(run_rule_300(edifici, areeverdi))"""