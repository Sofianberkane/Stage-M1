# Changer le répertoire de travail pour accéder aux fichiers de données
import os
os.chdir("C:/Users/sofian.berkane/Downloads/Soso/Code/data")

# Ajouter ce répertoire au chemin d'import pour les scripts locaux
import sys
sys.path.append("C:/Users/sofian.berkane/Downloads/Soso/Code/data")

import json
import numpy as np
import webbrowser
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from sklearn.cluster import KMeans
from collections import OrderedDict
from sklearn.metrics import pairwise_distances
from datetime import datetime, date, timedelta, time
from scipy.ndimage import uniform_filter1d
from sklearn.decomposition import PCA
from itertools import groupby
from operator import itemgetter
from pathlib import Path

# Fonctions de récupération des fichiers personnalisées
from rec_data_gps import recup_temps_pos
from recuperer_fichiers import charger_groupes_par_trajet_et_sens
from gps_utils import haversine_km


# name = "ligne_2"

# # Récupération des chemins vers les fichiers capteurs et GPS pour un trajet donné
# groupes = charger_groupes_par_trajet_et_sens(name, "sens_1")

# print(groupes)

# gps_path, capteurs_list = groupes[1]

# # print(groupes[3])

# # Extraction des données de position, vitesse et arrêts à partir du fichier GPS
# t, t_arret, idx_arret, loc, spd = recup_temps_pos(gps_path)



def analyse_capt(path, t, t_arret, idx_arret, nom_traj, loc, spd):
    # Lecture du fichier
    df = pd.read_csv(
        path,
        sep='\t',
        skiprows=8,   # saute jusqu'à la ligne 8 → arrive sur ligne des titres
        header=0,     # dit que cette ligne est le header
        engine='python'
    )
    
    
    df = df.loc[:, ~df.columns.isna()]
    df.columns = df.columns.str.replace('"', '').str.strip()
    
    col_time = 's'
    
    # Supprimer la ligne des unités AVANT conversion en datetime
    if df[col_time].dtype == object:
        df = df[~df[col_time].str.contains("s", na=False)]
    
    
    
    # Convertir en datetime avec gestion des erreurs
    df[col_time] = pd.to_datetime(df[col_time], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
    
    # Supprimer les lignes avec dates invalides
    df = df.dropna(subset=[col_time])
    df['datetime'] = df[col_time]    
    
    
    
    # Remplacer les cases vides ("") par NaN
    df.replace('', np.nan, inplace=True)
    
    # Puis remplir les NaN vers l’avant (forward fill)
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    
    
    
    
    # Conversion de t en datetime.time
    t_times = [datetime.strptime(h, "%H:%M:%S.%f").time() for h in t]
    
    if not t_times:
        raise ValueError("La liste des temps t est vide : impossible de déterminer la borne temporelle minimale.")
    
    heure_min = min(t_times)
    heure_max = max(t_times)
    
    df['heure_only'] = df['s'].dt.time
    
    if df['heure_only'].empty:
        raise ValueError("Le dataframe filtré n'a pas de temps valide : impossible de continuer.")
    
    df_heure_min = df['heure_only'].min()
    df_heure_max = df['heure_only'].max()
    
    # Calcul de l'intersection
    borne_debut = max(df_heure_min, heure_min)
    borne_fin   = min(df_heure_max, heure_max)
    
    print(f"Fenêtre commune : {borne_debut} --> {borne_fin}")
    
    # === Filtrage de df ===
    df_filtre = df[(df['heure_only'] >= borne_debut) & (df['heure_only'] <= borne_fin)]
    df_filtre = df_filtre.reset_index(drop=True)
    
    # === Filtrage de t ===
    # 1 Filtrage de t
    t_filtre = []
    t_arret_filtre = []
    loc_filtre = []
    spd_filtre = []
    
    
    for i, h_str in enumerate(t):
        h = datetime.strptime(h_str, "%H:%M:%S.%f").time()
        if borne_debut <= h <= borne_fin:
            t_filtre.append(h_str)
            loc_filtre.append(loc[i])
            spd_filtre.append(spd[i])
            
    for i, h_str in enumerate(t_arret):
        h = datetime.strptime(h_str, "%H:%M:%S.%f").time()
        if borne_debut <= h <= borne_fin:
            t_arret_filtre.append(h_str)
            
            
    # donnees_filtrees = OrderedDict()
    # donnees_filtrees["date"] = t_filtre
    # donnees_filtrees["localisation gps"] = loc_filtre
    # donnees_filtrees["vitesse"] = spd_filtre
    # donnees_filtrees["moment en arret"] = t_arret_filtre
    
    # with open("C:/Users/sofian.berkane/Downloads/Soso/data_test/IA/tableau_gps.json", "w", encoding="utf-8") as f:
    #     json.dump(donnees_filtrees, f, ensure_ascii=False, indent=4)
        
    
    df_filtre['Time_seconds'] = (df_filtre[col_time] - df_filtre[col_time].iloc[0]).dt.total_seconds()
    
    # colonnes_a_supprimer = df_filtre.columns[12:23]
    # df_filtre_reduit = df_filtre.drop(columns=colonnes_a_supprimer)
    
    # import math

    # # Nombre total de lignes
    # nb_total = len(df_filtre_reduit)
    
    # # Indice de séparation
    # milieu = math.ceil(nb_total / 2)  # arrondi vers le haut si impair
    
    # # Découpe du DataFrame
    # df_part1 = df_filtre_reduit.iloc[:milieu].reset_index(drop=True)
    # df_part2 = df_filtre_reduit.iloc[milieu:].reset_index(drop=True)
    
    # # Sauvegarde des deux moitiés
    # df_part1.to_csv("C:/Users/sofian.berkane/Downloads/Soso/data_test/IA/info_capteur_part1.csv", index=False)
    # df_part2.to_csv("C:/Users/sofian.berkane/Downloads/Soso/data_test/IA/info_capteur_part2.csv", index=False)

    
    t_arret_filtre = pd.to_datetime(t_arret_filtre, format='%H:%M:%S.%f').time
    df_filtre_time = df_filtre.s.dt.time
    
    
    
    
    # Convertir en datetime (si ce n'est pas déjà fait)
    t_arret_dt = [datetime.combine(date.today(), t) for t in t_arret_filtre]
    
    # Construire un DataFrame avec les intervalles successifs
    df_arrets = pd.DataFrame({
        'start': t_arret_dt[:-1],
        'end': t_arret_dt[1:]
    })
    
    
    
    # Garder uniquement ceux dont la durée est ≤ 1 seconde
    df_arrets = df_arrets[(df_arrets['end'] - df_arrets['start']).dt.total_seconds() <= 10]
    
    df_time_dt = pd.Series([datetime.combine(date.today(), t) for t in df_filtre_time])
    
    # Créer un tableau de booléens
    idx_stop = []
    
    # Pour chaque intervalle (start, end), on trouve les indices dans df_time_dt
    for start, end in zip(df_arrets['start'], df_arrets['end']):
        # Trouve tous les temps entre start et end
        mask = (df_time_dt > start) & (df_time_dt < end)
        idxs = df_time_dt[mask].index.tolist()
        idx_stop.extend(idxs)
        
    
        
    
    
    if len(t_arret_filtre) == 0:
        raise ValueError("Aucun arrêt détecté dans t_arret_filtre, impossible de corriger l’offset.")
    
    
    # Convertir t_arret_filtre (moments d’arrêt) en datetime sur la même date que df_filtre
    first_arret_time = datetime.combine(df_filtre['datetime'].dt.date.iloc[0], t_arret_filtre[0])
    
    # Différence absolue entre chaque ligne de df_filtre et le premier arrêt
    delta = abs(df_filtre['datetime'] - first_arret_time)
    
    # Index de la ligne la plus proche de ce premier arrêt
    idx_ref = delta.idxmin()
          
        
        
    # Colonnes des accéléros à corriger
    capt_cols = [
        "Unnamed: 23", "Unnamed: 24", "Unnamed: 25",  # capt1
        "Unnamed: 26", "Unnamed: 27", "Unnamed: 28",  # capt2
        "Unnamed: 29", "Unnamed: 30", "Unnamed: 31"   # capt3
    ]
    
    for col in capt_cols:
        if col in df_filtre.columns:
            # Correction en place dans df_filtre
            df_filtre[col] = df_filtre[col].astype(float) - df_filtre[col].astype(float).iloc[idx_ref]
        else:
            print(f"⚠️ Colonne {col} absente dans df_filtre, correction ignorée.")
    
    
        
    ###  CAPTEUR 1  ####

    capt1_x = df_filtre["Unnamed: 23"]
    capt1_x = capt1_x - capt1_x.iloc[idx_stop[0]]
    capt1_x_arr = capt1_x.iloc[idx_stop]- capt1_x.iloc[idx_stop[0]]
    
    capt1_y = df_filtre["Unnamed: 24"]
    capt1_y = capt1_y - capt1_y.iloc[idx_stop[0]]
    capt1_y_arr = capt1_y.iloc[idx_stop]- capt1_y.iloc[idx_stop[0]]
    
    capt1_z = df_filtre["Unnamed: 25"]
    capt1_z = capt1_z - capt1_z.iloc[idx_stop[0]]
    capt1_z_arr = capt1_z.iloc[idx_stop]- capt1_z.iloc[idx_stop[0]]
    
    
    ###  CAPTEUR 2  ###
    
    capt2_x = df_filtre["Unnamed: 26"]
    capt2_x = capt2_x - capt2_x.iloc[idx_stop[0]]
    capt2_x_arr = capt2_x.iloc[idx_stop]- capt2_x.iloc[idx_stop[0]]
    
    capt2_y = df_filtre["Unnamed: 27"]
    capt2_y = capt2_y - capt2_y.iloc[idx_stop[0]]
    capt2_y_arr = capt2_y.iloc[idx_stop]- capt2_y.iloc[idx_stop[0]]
    
    capt2_z = df_filtre["Unnamed: 28"]
    capt2_z = capt2_z - capt2_z.iloc[idx_stop[0]]
    capt2_z_arr = capt2_z.iloc[idx_stop]- capt2_z.iloc[idx_stop[0]]
    
    
    ###  CAPTEUR 3  ###
    
    capt3_x = df_filtre["Unnamed: 29"]
    capt3_x = capt3_x - capt3_x.iloc[idx_stop[0]]
    capt3_x_arr = capt3_x.iloc[idx_stop]- capt3_x.iloc[idx_stop[0]]
    
    capt3_y = df_filtre["Unnamed: 30"]
    capt3_y = capt3_y - capt3_y.iloc[idx_stop[0]]
    capt3_y_arr = capt3_y.iloc[idx_stop]- capt3_y.iloc[idx_stop[0]]
    
    capt3_z = df_filtre["Unnamed: 31"]
    capt3_z = capt3_z - capt3_z.iloc[idx_stop[0]]
    capt3_z_arr = capt3_z.iloc[idx_stop]- capt3_z.iloc[idx_stop[0]]
    
    ###  MICROPHONE 1  ###
    
    mic1_15_625  = df_filtre["dB(A)"]
    mic1_31_25   = df_filtre["dB(A).1"]
    mic1_62_5    = df_filtre["dB(A).2"]
    mic1_125     = df_filtre["dB(A).3"]
    mic1_250     = df_filtre["dB(A).4"]
    mic1_500     = df_filtre["dB(A).5"]
    mic1_1000    = df_filtre["dB(A).6"]
    mic1_2000    = df_filtre["dB(A).7"]
    mic1_4000    = df_filtre["dB(A).8"]
    mic1_8000    = df_filtre["dB(A).9"]
    mic1_16000   = df_filtre["dB(A).10"]
    
    
    ###  MICROPHONE 2  ###
    
    # mic2_15_625  = df_filtre["dB(A).11"]
    # mic2_31_25   = df_filtre["dB(A).12"]
    # mic2_62_5    = df_filtre["dB(A).13"]
    # mic2_125     = df_filtre["dB(A).14"]
    # mic2_250     = df_filtre["dB(A).15"]
    # mic2_500     = df_filtre["dB(A).16"]
    # mic2_1000    = df_filtre["dB(A).17"]
    # mic2_2000    = df_filtre["dB(A).18"]
    # mic2_4000    = df_filtre["dB(A).19"]
    # mic2_8000    = df_filtre["dB(A).20"]
    # mic2_16000   = df_filtre["dB(A).21"]
    
    
    virages_ligne_4 = {
        'Chaufferie_de_la_Doua': [(45.7820, 4.8757), (45.7818, 4.8751)],
        'Local_technique_Sytral': [(45.7818, 4.8751), (45.7817, 4.8745)],
        'Le_Prévert': [(45.7814, 4.8734), (45.7814, 4.8724)],
        'Triplet_av_Gaston_berger': [(45.7816, 4.8718), (45.7816, 4.8709)],
        'Triplet_Bibliothèque_Lyon_1': [(45.7816, 4.8709), (45.7816, 4.8700)],
        'Triplet_Double_av_Claude_Bernard': [(45.7816, 4.8700), (45.7815, 4.8692)],
        'Epingle_Geode': [(45.7808, 4.8661), (45.7802, 4.8657)],
        'Condorcet': [(45.7795, 4.8663), (45.7786, 4.8668)], 
        'Lakanal': [(45.7759, 4.8675), (45.7751, 4.8668)],
        'Doublet_du_Tonkin_loin': [(45.7745, 4.8653), (45.7742, 4.8648)],
        'Doublet_du_Tonkin_proche': [(45.7742, 4.8648), (45.7741, 4.8643)],
        'Maternelle_Nigritelle_Noir': [(45.7741, 4.8637),(45.7738, 4.8633)],
        'Doublet_Charpennes_Charles_Hernu': [(45.7709, 4.8630), (45.7701, 4.8624)],
        'Doublet_av_Thiers': [(45.7701, 4.8624), (45.7694, 4.8617)],
        'Potentielle_virage_Ehpad_ma_demeure': [(45.7636, 4.8621), (45.7622, 4.8620)],
        'Potentielle_virage_consulat_d_Autriche': [(45.7622, 4.8620), ( 45.7615, 4.8620)],
        'Doublet_hotel_police_Fort_Montluc': [(45.7534, 4.8618), (45.7508, 4.8608)],
        'Doublet_av_Général_Mouton_Duvernet': [(45.7508, 4.8608), (45.7504, 4.8604)],
        'Emmaus_connect': [(45.7426, 4.8583), (45.7407, 4.8587)],
        'La_Borelle': [(45.7121, 4.8810), (45.7113, 4.8819)],
        'Technicentre_SNCF': [(45.7082, 4.8869), (45.7062, 4.8877)],
        'Doublet_Croizat': [(45.7036, 4.8878), (45.7032, 4.8877)],
        'Doublet_entre_deux_bd_Croizart': [(45.7032, 4.8877), (45.7028, 4.8876)],
        'Av_Marcel_Houel': [(45.6973, 4.8876), (45.6969, 4.8870)],
        'Gymnase_Jacques_Brel': [(45.6963, 4.8831), (45.6953, 4.8804)],
        'Rond_point_av_Oschatz': [(45.6933, 4.8777), (45.6933, 4.8763)],
        'Rue_Alfred_de_Musset': [(45.6994, 4.8667), (45.6998, 4.8652)],
        'La_Rotonde': [(45.7000, 4.8610), (45.6993, 4.8603)],
        'Rue_Honoré_Daumier': [(45.6983, 4.8604), (45.6970, 4.8615)],
        'Rue_de_la_Corsière': [(45.6967, 4.8620), (45.6955, 4.8627)],
        'Allée_des_Jonquilles': [(45.6946, 4.8628), (45.6928, 4.8641)],
        'Pharmacie_Tchibozo': [(45.6925, 4.8645), (45.6918, 4.8652)],
        'Rue_Aimé_Césaire': [(45.6918, 4.8652),(45.6911, 4.8659)], 
        'Bioforce': [(45.6911, 4.8659), (45.6903, 4.8658)],
        'Institut_Jean_Jacques_Rousseau': [(45.6903, 4.8658), (45.6886, 4.8652)]}
    
    virages_ligne_1 = {
        'Bibliothèque_IUT': [(45.7854, 4.8826), (45.7852, 4.8829)],
        'Gymnase_IUT': [(45.7852, 4.8829), (45.7849, 4.8835)],
        'Croix_Luizet': [(45.7842, 4.8838), (45.7837, 4.8834)],
        'Chaufferie_de_la_Doua': [(45.7820, 4.8757), (45.7818, 4.8751)],
        'Local_technique_Sytral': [(45.7818, 4.8751), (45.7817, 4.8745)],
        'Le_Prévert': [(45.7814, 4.8734), (45.7814, 4.8724)],
        'Triplet_av_Gaston_berger': [(45.7816, 4.8718), (45.7816, 4.8709)],
        'Triplet_Bibliothèque_Lyon_1': [(45.7816, 4.8709), (45.7816, 4.8700)],
        'Triplet_Double_av_Claude_Bernard': [(45.7816, 4.8700), (45.7815, 4.8692)],
        'Epingle_Geode': [(45.7808, 4.8661), (45.7802, 4.8657)],
        'Condorcet': [(45.7795, 4.8663), (45.7786, 4.8668)], 
        'Lakanal': [(45.7759, 4.8675), (45.7751, 4.8668)],
        'Doublet_du_Tonkin_loin': [(45.7745, 4.8653), (45.7742, 4.8648)],
        'Doublet_du_Tonkin_proche': [(45.7742, 4.8648), (45.7741, 4.8643)],
        'Maternelle_Nigritelle_Noir': [(45.7741, 4.8637),(45.7738, 4.8633)],
        'Doublet_Charpennes_Charles_Hernu': [(45.7709, 4.8630), (45.7701, 4.8624)],
        'Doublet_av_Thiers': [(45.7701, 4.8624), (45.7694, 4.8617)],
        'Banque_Rhône_Alpes': [(45.7642, 4.8620), (45.7638, 4.8615)],
        'Main_tendue_d_Arman': [(45.7637, 4.8587), (45.7624, 4.8577)],
        'Place_Charles_Béraudier': [(45.7615, 4.8579), (45.7610, 4.8573)],
        'Grand_café_de_la_préfecture': [(45.7600, 4.8429), (45.7595, 4.8424)],
        'Guillotière': [(45.7558, 4.8429), (45.7551, 4.8426)],
        'Mychezmoi': [(45.7513, 4.8399), ( 45.7511, 4.8391)],
        'Université_Jean_Moulin': [(45.7517, 4.8375), (45.7516, 4.8368)],
        'Indy_Light': [(45.7483, 4.8342), (45.7481, 4.8332)],
        'Tram_33': [(45.7496, 4.8284), (45.7498, 4.8280)],
        'Perrache_termie_1': [(45.7498, 4.8280), (45.7496, 4.8271)],
        'Perrache_termie_6': [(45.7494, 4.8270), (45.7491, 4.8266)],
        'Pharmacie_Perrache': [(45.7491, 4.8266), (45.7488, 4.8261)],
        'Gare_Lyon_Perrache_voie_H': [(45.7479, 4.8254), (45.7476, 4.8251)],
        'Place_des_archives': [(45.7476, 4.8251), (45.7473, 4.8247)],
        'Station_Mue': [(45.7390, 4.8177), (45.7360, 4.8170)],
        'Passage_Magellan': [(45.7345, 4.8177), (45.7337, 4.8185)],
        'Musée_des_confluences': [(45.7335, 4.8192), (45.7331, 4.8199)],
        'Canoe_kayak_Ouillins_la_Mulatière': [(45.7321, 4.8212), (45.7319, 4.8220)],
        'Halle_Tony_Garnier': [(45.7317, 4.8232), (45.7316, 4.8237)],
        'Optique_Gerland': [(45.7313, 4.8332), (45.7313, 4.8337)],
        'Debourg': [(45.7313, 4.8337),(45.7313, 4.8343)]}
    
    virages_ligne_5 = {
        'Pharmacie_Rockefeller': [(45.7425, 4.8778), (45.7426, 4.8784)],
        'Permis_Malin': [(45.7418, 4.8832), (45.7419, 4.8828)],
        'Rue_Volney': [(45.7418, 4.8832), (45.7416, 4.8837)],
        'Centre_médical_Ambroise_Paré': [(45.7413, 4.8847), (45.7412, 4.8853)],
        'Résidence_Esquirol_Rockefeller': [(45.7412, 4.8853), (45.7411, 4.8858)],
        'La_Station': [(45.7391, 4.8919), (45.7390, 4.8924)],
        'Desgenettes': [(45.7390, 4.8924), (45.7389, 4.8929)],
        'Unité_pour_malades_difficiles': [(45.7364, 4.9008), (45.7361, 4.9014)],
        'Médiathèque_Jean_Pérvost': [(45.7361, 4.9014), (45.7358, 4.9020)],
        'Résidence_Arcole': [(45.7308, 4.9169), (45.7309, 4.9175)],
        'Foyer Henri Thomas': [(45.7319, 4.9181), (45.7329, 4.9181)],
        '1_rue_st_Denis': [(45.7332, 4.9179), (45.7339, 4.9176)],
        'Eglise_st_Denis': [(45.7361, 4.9169), (45.7370, 4.9175)],
        'Rond_point_rue_du_Chêne': [(45.7391, 4.9270), (45.7391, 4.9275)],
        '1_rue_du_Chêne': [(45.7391, 4.9275), (45.7392, 4.9281)],
        '59_rue_du_Chêne': [(45.7395, 4.9336), (45.7395, 4.9345)],
        'ZAC_du_Chêne': [(45.7392, 4.9351),(45.7390, 4.9357)],
        'Boulevard_Charles_de_Gaulle': [(45.7390, 4.9357), ( 45.7388, 4.9364)],
        'Golf_11': [(45.7383, 4.9375), (45.7381, 4.9396)],
        'Golf_10': [(45.7385, 4.9416), (45.7382, 4.9438)],
        'Golf_2': [(45.7379, 4.9443),(45.7370, 4.9453)],
        'Eurexpo': [(45.7337, 4.9468), (45.7333, 4.9470)]}
    
    virages_ligne_2 = {
        'Perrache_termie_1': [(45.7498, 4.8280), (45.7496, 4.8271)],
        'Tram_33': [(45.7496, 4.8284), (45.7498, 4.8280)],
        'Eglise_st_Marc': [(45.7366, 4.8688), (45.7368, 4.8700)],
        'Pharmacie_Rockefeller': [(45.7425, 4.8778), (45.7426, 4.8784)],
        'Permis_Malin': [(45.7418, 4.8832), (45.7419, 4.8828)],
        'Rue_Volney': [(45.7418, 4.8832), (45.7416, 4.8837)],
        'Centre_médical_Ambroise_Paré': [(45.7413, 4.8847), (45.7412, 4.8853)],
        'Résidence_Esquirol_Rockefeller': [(45.7412, 4.8853), (45.7411, 4.8858)],
        'La_Station': [(45.7391, 4.8919), (45.7390, 4.8924)],
        'Desgenettes': [(45.7390, 4.8924), (45.7389, 4.8929)],
        'Unité_pour_malades_difficiles': [(45.7364, 4.9008), (45.7361, 4.9014)],
        'Médiathèque_Jean_Pérvost': [(45.7361, 4.9014), (45.7358, 4.9020)],
        'Résidence_Arcole': [(45.7308, 4.9169), (45.7304, 4.9172)],
        'Jardin_du_mas_Rébufer': [(45.7273, 4.9156), (45.7268, 4.9154)],
        'Aldi': [(45.7263, 4.9153), (45.7258, 4.9152)],
        'Rond_point_bd_de_l_Université': [(45.7251, 4.9151), (45.7246, 4.9151)],
        'Bâtiment_T': [(45.7236, 4.9151), (45.7228, 4.9150)],
        'Parilly_Université_Hippodrome': [(45.7232, 4.9150), (45.7223, 4.9151)],
        'Europe_Université': [(45.7199, 4.9171), (45.7196, 4.9180)],
        'Batiment_O': [(45.7197, 4.9185), (45.7198, 4.9193)],
        'Chemin_de_la_côte': [(45.7199, 4.9200), (45.7202, 4.9222)],
        'Porte_des_Alpes': [(45.7202, 4.9222), (45.7199, 4.9235)],
        'Le_Cocon': [(45.7157, 4.9298), (45.7152, 4.9303)],
        'Sentier_de_Feuilly': [(45.7152, 4.9303), (45.7146, 4.9308)],
        'Rond_point_de_l_aviation': [(45.7097, 4.9382), (45.7082, 4.9378)],
        'Villas_du_parc': [(45.7077, 4.9365), (45.7064, 4.9349)],
        'Pizzas_du_Feuilly': [(45.7064, 4.9349), (45.7060, 4.9348)],
        'Place_Hélène_Boucher': [(45.7060, 4.9348), (45.7053, 4.9346)],
        'Square_Hubert_Hélias': [(45.7032, 4.9349), (45.7027, 4.9351)],
        '20_rue_Slavador_Allende': [(45.7027, 4.9351), (45.7022, 4.9354)],
        'Le_Swann': [(45.7017, 4.9356), (45.7010, 4.9358)],
        'Alfred_Vigny': [(45.7005, 4.9358), (45.6998, 4.9360)],
        'Alfred_Vigny_bus': [(45.6994, 4.9362), (45.6990, 4.9363)],
        '46_rue_Alfred_Vigny': [(45.6987, 4.9363), (45.6984, 4.9363)],
        '56_rue_Alfred_Vigny': [(45.6984, 4.9363), (45.6981, 4.9362)],
        'Ermitage': [(45.6955, 4.9359), (45.6951, 4.9365)],
        'Grand_scénario': [(45.6950, 4.9373), (45.6948, 4.9379)],
        'Gymnase_Léon_Perrier': [(45.6948, 4.9379), (45.6946, 4.9384)],
        'Seven_shopping': [(45.6946, 4.9384), (45.6946, 4.9392)],
        'Rue_de_l_Egalité': [(45.6941, 4.9446), (45.6946, 4.9467)],
        'Ecole_maternelle_Jules_Ferry': [(45.6948, 4.9470), (45.6949, 4.9478)],
        '20_rue_de_la_Cordière': [(45.6944, 4.9488), (45.6942, 4.9492)],
        '26_rue_de_la_Cordière': [(45.6942, 4.9492), (45.6938, 4.9495)],
        'Fast_lodge_Lyon_est_Eurexpo': [(45.6935, 4.9499), (45.6932, 4.9511)],
        '42_rue_de_la_Cordière': [(45.6932, 4.9513), (45.6929, 4.9529)],
        'T12': [(45.6929, 4.9529), (45.6927, 4.9541)],
        }
    
    virages_ligne_6 = {
        'Fryd-Gerland': [(45.7303, 4.8375), (45.7300, 4.8388)],
        'T6': [(45.7294, 4.8467), (45.7294, 4.8479)],
        'Une_rue_Challemem-Lacour': [(45.7294, 4.8501), (45.7294, 4.8507)],
        'Deux_rue_Challemem-Lacour': [(45.7294, 4.8507), (45.7293, 4.8513)],
        'Moulin_à_vent': [(45.7293, 4.8522), (45.7295, 4.8528)],
        'Petite_Guille': [(45.7311, 4.8591), (45.7309, 4.8598)],
        'Pharmacie_Coche_Maison': [(45.7305, 4.8600), (45.7300, 4.8602)],
        'Beauvisage_Pressensé': [(45.7278, 4.8617), (45.7276, 4.8624)],
        'Mermoz_Californie': [(45.7332, 4.8788), (45.7331, 4.8795)],
        'Mermoz_Pinel': [(45.7307, 4.8871), (45.7310, 4.8879)],
        'Pharmacie_provisoire': [(45.7310, 4.8879), (45.7335, 4.8889)],
        'Bureau_des_entrée': [(45.7416, 4.8935), (45.7420, 4.8937)],
        'Vinatier': [(45.7420, 4.8937), (45.7423, 4.8940)],
        'Square_Farrère': [(45.7428, 4.8943), (45.7434, 4.8947)],
        'Hopital_Desgnettes_Vinatier': [(45.7434, 4.8947), (45.7439, 4.8950)],
        'Institut_des_sciences_cognitives': [(45.7466, 4.8964), (45.7473, 4.8967)]}
    
    virages_ligne_3 = {
        'Part_Dieu': [(45.7564, 4.8619), (45.7562, 4.8619)],
        'Double_rue_Général_Mouton_1': [(45.7562, 4.8619), (45.7560, 4.8619)],
        'Double_rue_Général_Mouton_2': [(45.7557, 4.8619), (45.7553, 4.8619)],
        'Archives_départementales': [(45.7553, 4.8619), (45.7548, 4.8623)],
        'Collège_Gilbert_Dru': [(45.7539, 4.8639), (45.7532, 4.8665)],
        'Ramsay_santé': [(45.7527, 4.8706), (45.7525, 4.8734)],
        'Parc_Georges_Bazin': [(45.7529, 4.8798), (45.7538, 4.8837)],
        'Reconnaissance_Balzac': [(45.7547, 4.8854), (45.7553, 4.8875)],
        'Parling': [(45.7587, 4.9124), (45.7591, 4.9145)],
        'Gifrer_Barbezat': [(45.7671, 4.9465), (45.7690, 4.9510)],
        '34_rue_Edison': [(45.7736, 4.9589), (45.7748, 4.9612)],
        'Prairie_de_la_Berthaudière': [(45.7770, 4.9667), (45.7765, 4.9728)],
        'Décines_grand_large': [(45.7755, 4.9742), (45.7748, 4.9757)],
        'Parc_relais_TCL_Déclines_grand_large': [(45.7746, 4.9763), (45.7742, 4.9777)]}
    
    
    
    ############################ Avoir info virages ########################################
    # Convertir ta liste t_filtre en datetime
    reference_date = df_filtre['datetime'].dt.date.iloc[0]
    
    if nom_traj == "ligne_1":
        nom = virages_ligne_1
    elif nom_traj == "ligne_2":
        nom = virages_ligne_2
    elif nom_traj == "ligne_3":
        nom = virages_ligne_3
    elif nom_traj == "ligne_4":
        nom = virages_ligne_4
    elif nom_traj == "ligne_5":
        nom = virages_ligne_5
    else:
        nom = virages_ligne_6
    
    # Dictionnaire pour accumuler les lignes par virage
    # === Dictionnaire pour stocker les lignes de stats par virage
    tableaux_virages = {}
    
    for nom_virage, (coord_start, coord_end) in nom.items():
        # Trouver les indices dans loc_filtre les plus proches des coordonnées GPS du virage
        min_dist_start, idx_start_loc = float('inf'), None
        for i, point in enumerate(loc_filtre):
            if None in point or np.nan in point:
                continue
            dist = haversine_km(point, coord_start)
            if dist < min_dist_start:
                min_dist_start, idx_start_loc = dist, i
    
        min_dist_end, idx_end_loc = float('inf'), None
        for i, point in enumerate(loc_filtre):
            if None in point or np.nan in point:
                continue
            dist = haversine_km(point, coord_end)
            if dist < min_dist_end:
                min_dist_end, idx_end_loc = dist, i
        
        # Vérifie que le tram s'est réellement approché du virage
        if min_dist_start > 0.02 or min_dist_end > 0.02:  # seuil à 20 mètres
            print(f"🚫 Virage {nom_virage} ignoré : trop loin (distances {min_dist_start*1000:.1f}m, {min_dist_end*1000:.1f}m)")
            continue

    
        if idx_start_loc is None or idx_end_loc is None:
            print(f"❗ Aucun passage détecté pour {nom_virage}")
            continue
    
        # Sécurité : inverser si ordre incohérent
        if idx_start_loc > idx_end_loc:
            idx_start_loc, idx_end_loc = idx_end_loc, idx_start_loc
    
        # ➔ Conversion en temps absolus
        t_start_abs = datetime.combine(reference_date, datetime.strptime(t_filtre[idx_start_loc], "%H:%M:%S.%f").time())
        t_end_abs   = datetime.combine(reference_date, datetime.strptime(t_filtre[idx_end_loc], "%H:%M:%S.%f").time())
    
        # ➔ Trouver les indices dans df_filtre (repère des capteurs)
        idx_start_capteur = (df_filtre["datetime"] - t_start_abs).abs().idxmin()
        idx_end_capteur   = (df_filtre["datetime"] - t_end_abs).abs().idxmin()
        if idx_start_capteur >= len(df_filtre) or idx_end_capteur >= len(df_filtre):
            print("❗ Indices capteurs hors bornes pour le virage, ignoré.")
            continue
    
        print(f"⏱️ Virage {nom_virage} indices capteurs : {idx_start_capteur} → {idx_end_capteur} "
              f"(GPS distances {min_dist_start*1000:.1f}m, {min_dist_end*1000:.1f}m)")
    
        # Découpe des intervalles corrects
        interval_capt1_x = capt1_x.iloc[idx_start_capteur:idx_end_capteur+1]
        interval_capt1_y = capt1_y.iloc[idx_start_capteur:idx_end_capteur+1]
        interval_capt1_z = capt1_z.iloc[idx_start_capteur:idx_end_capteur+1]
        interval_capt2_x = capt2_x.iloc[idx_start_capteur:idx_end_capteur+1]
        interval_capt2_y = capt2_y.iloc[idx_start_capteur:idx_end_capteur+1]
        interval_capt2_z = capt2_z.iloc[idx_start_capteur:idx_end_capteur+1]
        interval_capt3_x = capt3_x.iloc[idx_start_capteur:idx_end_capteur+1]
        interval_capt3_y = capt3_y.iloc[idx_start_capteur:idx_end_capteur+1]
        interval_capt3_z = capt3_z.iloc[idx_start_capteur:idx_end_capteur+1]
        
        
        # Stats accéléros
        acc_stats = {}
        for name, interval in zip(
            ["capt1_x", "capt1_y", "capt1_z", "capt2_x", "capt2_y", "capt2_z", "capt3_x", "capt3_y", "capt3_z"],
            [interval_capt1_x, interval_capt1_y, interval_capt1_z,
             interval_capt2_x, interval_capt2_y, interval_capt2_z,
             interval_capt3_x, interval_capt3_y, interval_capt3_z]):
            acc_stats[f"{name}_max"] = interval.abs().max()
    
    
        # Stats microphones
        mic_stats = {}
        mic_vars = [
            mic1_15_625, mic1_31_25, mic1_62_5, mic1_125, mic1_250, mic1_500,
            mic1_1000, mic1_2000, mic1_4000, mic1_8000, mic1_16000
        ]
        
        mic_names = [
            "mic1_15_625","mic1_31_25","mic1_62_5","mic1_125","mic1_250","mic1_500",
            "mic1_1000","mic1_2000","mic1_4000","mic1_8000","mic1_16000"
        ]
    
        for name, var in zip(mic_names, mic_vars):
            interval = var.iloc[idx_start_capteur:idx_end_capteur+1]
            mic_stats[f"{name}_max"] = interval.max()
        
        # Découpe des vitesses dans l'intervalle GPS
        interval_vitesse = spd_filtre[idx_start_loc:idx_end_loc+1]
        
        if len(interval_vitesse) > 0:
            vmax = max(interval_vitesse)
        else:
            vmax = np.nan
            
    
        
        # Coordonnées GPS associées au début et à la fin du virage
        lat_debut, lon_debut = loc_filtre[idx_start_loc]
        lat_fin, lon_fin = loc_filtre[idx_end_loc]
        
        
        # Construire la ligne de stats
        ligne = {
            "date": df_filtre["datetime"].iloc[idx_start_capteur].date(),
            "heure_debut": df_filtre["datetime"].iloc[idx_start_capteur].time().strftime("%H:%M:%S.%f")[:-3],
            "heure_fin": df_filtre["datetime"].iloc[idx_end_capteur].time().strftime("%H:%M:%S.%f")[:-3],
            "lat_debut": lat_debut,
            "lon_debut": lon_debut,
            "idx_start_gps": idx_start_loc,
            "idx_end_gps": idx_end_loc,
            "idx_start_capt": idx_start_capteur,
            "idx_end_capt": idx_end_capteur,
            "vitesse_max": vmax,
            **acc_stats,
            **mic_stats
        }
    
        if nom_virage not in tableaux_virages:
            tableaux_virages[nom_virage] = []
        tableaux_virages[nom_virage].append(ligne)
        
    
    ####################################### Avoir info ligne droite ##################################
    intervals_virages = []
    for lignes in tableaux_virages.values():
        for ligne in lignes:
            idx_start = ligne["idx_start_gps"]
            idx_end = ligne["idx_end_gps"]
            intervals_virages.append((idx_start, idx_end))
    
    occupes = []

    # Ajoute intervalles de virages
    for start, end in intervals_virages:
        occupes.append((start, end))
    
    # Ajoute les arrêts (traités comme intervalles d'un point)
    for idx in idx_arret:
        occupes.append((idx, idx))
    
    # 2) Trie par début d'intervalle
    occupes.sort()
    
    # 3) Parcourt la timeline et repère les "trous" = lignes droites
    lignes_droites = []
    fin_prec = 0
    seuil_points = 30
    
    for start, end in occupes:
        if start - fin_prec >= seuil_points:  
            lignes_droites.append((fin_prec, start-1))
        fin_prec = max(fin_prec, end+1)
    
    # 4) Dernier segment jusqu’à la fin
    if len(t_filtre)-1 - fin_prec >= seuil_points:
        lignes_droites.append((fin_prec, len(t_filtre)-1))
        
        
        
    stats_lignes_droites = []

    for idx_start_loc, idx_end_loc in lignes_droites:
        # 1) Vérifie bornes GPS
        if idx_start_loc >= len(t_filtre) or idx_end_loc >= len(t_filtre):
            print(f"❗ Lignes droites: indices GPS hors bornes ({idx_start_loc} → {idx_end_loc}), ignorée.")
            continue
        
        # 2) Convertis indices GPS en temps absolu
        t_start_abs = datetime.combine(reference_date, datetime.strptime(t_filtre[idx_start_loc], "%H:%M:%S.%f").time())
        t_end_abs = datetime.combine(reference_date, datetime.strptime(t_filtre[idx_end_loc], "%H:%M:%S.%f").time())
        
        # 3) Trouve les indices correspondants dans le dataframe capteur
        idx_start_capteur = (df_filtre["datetime"] - t_start_abs).abs().idxmin()
        idx_end_capteur = (df_filtre["datetime"] - t_end_abs).abs().idxmin()
        
        if idx_start_capteur >= len(df_filtre) or idx_end_capteur >= len(df_filtre):
            print("❗ Indices capteurs hors bornes pour ligne droite, ignorée.")
            continue
        
        # 4) Stats sur vitesse dans l’intervalle GPS
        interval_vitesse = spd_filtre[idx_start_loc:idx_end_loc+1]
        vmax = max(interval_vitesse) if len(interval_vitesse) > 0 else np.nan
        
        # 5) Stats sur capteurs (interval capteur)
        acc_stats = {}
        for name, interval in zip(
            ["capt1_x", "capt1_y", "capt1_z", "capt2_x", "capt2_y", "capt2_z", "capt3_x", "capt3_y", "capt3_z"],
            [capt1_x, capt1_y, capt1_z, capt2_x, capt2_y, capt2_z, capt3_x, capt3_y, capt3_z]):
            sub = interval.iloc[idx_start_capteur:idx_end_capteur+1]
            acc_stats[f"{name}_max"] = sub.abs().max() if not sub.empty else np.nan
        
        mic_stats = {}
        for name, var in zip(
            mic_names,
            [mic1_15_625, mic1_31_25, mic1_62_5, mic1_125, mic1_250, mic1_500,
             mic1_1000, mic1_2000, mic1_4000, mic1_8000, mic1_16000]):
            sub = var.iloc[idx_start_capteur:idx_end_capteur+1]
            mic_stats[f"{name}_max"] = sub.max() if not sub.empty else np.nan
            
        
        stats_lignes_droites.append({
            "date": t_start_abs.date(),
            "idx_start_gps": idx_start_loc,
            "idx_end_gps": idx_end_loc,
            "heure_debut": t_start_abs.time().strftime("%H:%M:%S.%f")[:-3],
            "heure_fin": t_end_abs.time().strftime("%H:%M:%S.%f")[:-3],
            "vitesse_max": vmax,
            **acc_stats,
            **mic_stats
        })
        
    ##################################### Interpolation #####################################
    mic_vars = [
        mic1_15_625, mic1_31_25, mic1_62_5, mic1_125, mic1_250, mic1_500,
        mic1_1000, mic1_2000, mic1_4000, mic1_8000, mic1_16000
    ]
    mic_names = [
        "mic1_15_625","mic1_31_25","mic1_62_5","mic1_125","mic1_250","mic1_500",
        "mic1_1000","mic1_2000","mic1_4000","mic1_8000","mic1_16000"
    ]

    # Construire une fois pour toutes le tableau numpy des temps GPS absolus (au lieu de le reconstruire à chaque boucle)
    t_gps_abs = np.array([
        datetime.combine(reference_date, datetime.strptime(t, "%H:%M:%S.%f").time())
        for t in t_filtre
    ])
    
    t0 = t_gps_abs[0]
    t_gps_seconds = np.array([(ti - t0).total_seconds() for ti in t_gps_abs])
    
    df_valide = df_filtre[df_filtre["datetime"].notnull()]

    # Récupérer les datetimes sous forme de numpy array
    t_capt_dt = df_valide["datetime"].to_numpy()
    
    # Uniformiser les types : convertir numpy.datetime64 en pandas.Timestamp
    t_capt_dt = np.array([
        pd.Timestamp(ti) if isinstance(ti, np.datetime64) else ti
        for ti in t_capt_dt
    ])
    
    # Calculer les temps en secondes
    t_capt_seconds = np.array([(ti - t0).total_seconds() for ti in t_capt_dt])
    
    # 3) Interpoler la vitesse aux temps capteurs
    spd_filtre_arr = np.array(spd_filtre)
    spd_interp = np.interp(
        t_capt_seconds,
        t_gps_seconds,
        spd_filtre_arr
    )
    
    
    longitudes = [lon[0] for lon in loc_filtre]
    latitudes = [lat[1] for lat in loc_filtre]
    
    lon_interp = np.interp(
        t_capt_seconds,
        t_gps_seconds,
        longitudes
    )
    lat_interp = np.interp(
        t_capt_seconds,
        t_gps_seconds,
        latitudes
    )
    
    loc_interp = list(zip(lon_interp, lat_interp))
    
    #############################################################################
    
    mic_name = ["dB(A).7","dB(A).8"]
        
    
    df = pd.DataFrame({
        'vitesse': spd_interp,
        '15 Hz': mic1_15_625,
        '31 Hz': mic1_31_25,
        '63 Hz': mic1_62_5,
        '125 Hz': mic1_125,
        '250 Hz': mic1_250,
        '500 Hz': mic1_500,
        '1000 Hz': mic1_1000,
        '2000 Hz': mic1_2000,
        '4000 Hz': mic1_4000,
        '8000 Hz': mic1_8000,
        '16000 Hz': mic1_16000
    })
    
    # corr_matrix = df.corr()
    # plt.figure(figsize=(14, 12))  # Taille adaptée
    # sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', square=True,
    #             cbar_kws={"shrink": 0.8}, linewidths=0.5, linecolor='gray')
    # plt.title("Matrice de corrélation")
    # plt.tight_layout()  # Pour éviter que les labels soient coupés
    # plt.subplots_adjust(bottom=0.25)
    # plt.show()
    
    
    
    # for mic in mic_name:
    #     serie = df_filtre[mic]
    #     coeffs = np.polyfit(np.log10(spd_interp), serie, deg=1)  # polynôme de degré 2
    #     a,b=coeffs
        
    #     def log10_mdel(x):
    #         return a*np.log10(x)+b
    
        
    #     # Valeurs prédites par la tendance
    #     predicted = log10_mdel(spd_interp)
        
    #     residuals = serie - predicted
        
    #     mean_res = np.mean(residuals)
    #     std_res = np.std(residuals)
    #     threshold = mean_res + 2 * std_res
        
    #     anomalies = residuals > threshold
        
    #     idx_sorted = np.argsort(spd_interp)   
    #     spd_sorted = spd_interp[idx_sorted]     
    #     mic_sorted =predicted[idx_sorted]
        
    #     plt.figure(figsize=(8,6))
    #     plt.scatter(spd_interp, serie, s=2, label="Mesures")
        
    #     plt.plot(spd_sorted, mic_sorted, color="orange", label="Tendance")
        
    #     plt.scatter(spd_interp[anomalies], serie.values[anomalies], facecolors='none', edgecolors='r', s=50, label="Anomalies")
    #     plt.xlabel("Vitesse")
    #     plt.ylabel("Niveau sonore (dB(A))")
    #     plt.legend()
    #     plt.title(f"Détection d'anomalies par écart à la tendance - {mic} ")
    #     plt.grid()
    #     plt.show()
        
        
    #     plt.figure()
    #     plt.scatter(
    #         lon_interp[~anomalies], 
    #         lat_interp[~anomalies], 
    #         c=df_filtre[mic][~anomalies], 
    #         cmap='viridis', 
    #         s=10,
    #         label="Normal"
    #     )
        
    #     # Scatter anomalies (en rouge)
    #     plt.scatter(
    #         lon_interp[anomalies], 
    #         lat_interp[anomalies], 
    #         color='red', 
    #         s=20, 
    #         label="Anomalies"
    #     )
        
    #     plt.xlabel('Longitude')
    #     plt.ylabel('Latitude')
    #     plt.title(f'Intensité sonore et anomalies - {mic}')
    #     plt.grid()
    #     plt.axis('equal')
    #     plt.legend()
    #     plt.show()
        
        
        
    ############################# Avoir anomalies accéléro #################################
    # Regrouper les séries dans un dictionnaire
    series_dict = {
        "capt1_x": capt1_x,
        "capt2_x": capt2_x,
        "capt3_x": capt3_x,
        "capt1_z": capt1_z,
        "capt2_z": capt2_z,
        "capt3_z": capt3_z
    }
    
    # Seuils
    seuils = {
        "_x": 0.150,
        "_z": 0.200
    }
    
    # Résultat stocké ici
    depassements = {}
    
    for name, serie in series_dict.items():
        for axe, seuil in seuils.items():
            if axe in name:
                mask = serie.abs() > seuil
                indices = serie[mask].index
                valeurs = serie[mask].values
    
                depassements[name] = [
                    {"index": idx, "value": val, "vitesse": spd_interp[idx]}
                    for idx, val in zip(indices, valeurs)
                ]
                break
    
    # m = folium.Map(location=loc_interp[0], zoom_start=14)
    # folium.PolyLine(loc_interp, color='blue', weight=4).add_to(m)
    # # Ajout des cercles
    # for capteur, liste_depassements in depassements.items():
    #     for dep in liste_depassements:
    #         index = dep["index"]
    #         valeur = dep["value"]
    #         vitesse = dep["vitesse"]
    #         folium.Circle(
    #             location=loc_interp[index],
    #             radius=5,
    #             color='red',
    #             fill=True,
    #             fill_opacity=0.6,
    #             popup=f"Vitesse: {vitesse} \n Accèl: {valeur}"
    #         ).add_to(m)
            
    # # Sauvegarde et ouverture
    # m.save("C:/Users/sofian.berkane/Downloads/carte_anomalies_accel.html")
    
    return tableaux_virages, stats_lignes_droites, loc_filtre, loc_interp, depassements




# tableau = analyse_capt(capteurs_list[0], t, t_arret, idx_arret ,name, loc, spd)

