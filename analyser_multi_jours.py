# Changer le répertoire de travail pour accéder aux fichiers de données
import os
os.chdir("C:/Users/sofian.berkane/Downloads/Soso/Code/data")

# Ajouter ce répertoire au chemin d'import pour les scripts locaux
import sys
sys.path.append("C:/Users/sofian.berkane/Downloads/Soso/Code/data")

from pathlib import Path
import pandas as pd
from rec_data_capt import analyse_capt
from recuperer_fichiers import charger_groupes_par_trajet_et_sens
from rec_data_gps import recup_temps_pos
import matplotlib.pyplot as plt
import folium
from collections import Counter, defaultdict
from geopy.distance import geodesic
import webbrowser


def analyse_multi(trajet, sens):
    
    # Récupérer tous les couples GPS-capteurs pour ce trajet/sens
    groupes = charger_groupes_par_trajet_et_sens(trajet, sens)
    recurence = round(len(groupes)/2)
    
    # Dictionnaire global pour accumuler toutes les lignes par virage
    tableaux_globaux = {}
    lignes_droites_global = {}
    anomaly_clusters_by_freq = defaultdict(list)
    depassements_par_capteur = defaultdict(list)
    
    # Boucle sur chaque groupe (GPS + capteurs) trouvé
    for gps_path, capteurs_list in groupes:
        print(f"\n=== Analyse pour GPS: {gps_path.name} ===")
        for capteur in capteurs_list:
            print(f"  → Capteur : {capteur.name}")
            try:
                # Appel de ta fonction principale d'analyse
                t, t_arret, idx_arret, loc, spd = recup_temps_pos(gps_path)
                tableaux_virages, stats_lignes_droites, loc_filtre, loc_interp, anomalies_son, anomalies_accel = analyse_capt(capteur, t, t_arret, idx_arret, 
                                                                                                                              trajet, loc, spd)
                
                if tableaux_virages:
                    # Prend la première clé (virage) et extrait la date associée
                    first_virage_key = next(iter(tableaux_virages))
                    if tableaux_virages[first_virage_key]:
                        file_date = tableaux_virages[first_virage_key][0].get("date", "inconnue")
                    else:
                        file_date = "inconnue"
                else:
                    file_date = "inconnue"
                    
                
                # Fusionne les résultats dans le tableau global
                for virage, lignes in tableaux_virages.items():
                    if virage not in tableaux_globaux:
                        tableaux_globaux[virage] = []
                    tableaux_globaux[virage].extend(lignes)
                
                
                for ligne in stats_lignes_droites:
                    date_key = ligne["date"]
                    if date_key not in lignes_droites_global: 
                        lignes_droites_global[date_key] = []
                    lignes_droites_global[date_key].append(ligne)
                
                # Pour chaque fréquence : détecter les positions GPS associées
                for freq, indices in anomalies_son.items():
                    positions = set()
                    for idx in indices:
                        if idx < len(loc_interp):
                            positions.add(tuple(loc_interp[idx]))
                
                    # Mise à jour des clusters pour cette fréquence
                    for pos in positions:
                        found = False
                        for cluster in anomaly_clusters_by_freq[freq]:
                            if geodesic(pos, cluster["position"]).meters <= 5:
                                if "files_seen" not in cluster:
                                    cluster["files_seen"] = set()
                                if capteur.name not in cluster["files_seen"]:
                                    cluster["files_seen"].add(capteur.name)
                                    cluster["count"] += 1
                                found = True
                                break
                        if not found:
                            anomaly_clusters_by_freq[freq].append({
                                "position": pos,
                                "count": 1,
                                "files_seen": {capteur.name}
                            })
                
                
                for capteur_name, evenements in anomalies_accel.items():
                    for evt in evenements:
                        evt["date"] = file_date
                        if "file" in evt:
                            del evt["file"]
                
                for capteur_name, evenements in anomalies_accel.items():
                    depassements_par_capteur[capteur_name].extend(evenements)

                
                
                
                
                # # ➔ Génération d'une carte pour ce fichier (si loc non vide)
                # if loc:
                #     # Créer la carte centrée sur le premier point GPS
                #     lat0, lon0 = loc_filtre[0]
                #     m = folium.Map(location=(lat0, lon0), zoom_start=14, tiles="OpenStreetMap")
                #     m.add_child(folium.LatLngPopup())
                    
                #     # Tracer tous les arrêts en bleu
                #     for idx in idx_arret:
                #         lat, lon = loc_filtre[idx]
                #         folium.CircleMarker(
                #             location=(lat, lon),
                #             radius=3,
                #             color='blue',
                #             fill=True,
                #             fill_opacity=0.7,
                #             popup="Arrêt"
                #         ).add_to(m)
                    
                #     # Tracer tous les arrêts en bleu
                #     for lignes in val_crit:
                #         coords = loc_filtre[lignes["idx_gps"]]
                #         folium.CircleMarker(
                #             location=coords,
                #             radius=3,
                #             color='black',
                #             fill=True,
                #             fill_opacity=0.7,
                #             popup="Critique"
                #         ).add_to(m)
                    
                #     # Tracer tous les virages en orange
                #     for virage, lignes in tableaux_virages.items():
                #         for ligne in lignes:
                #             idx_start = ligne["idx_start_gps"]
                #             idx_end = ligne["idx_end_gps"]
                #             coords = [loc_filtre[i] for i in range(idx_start, idx_end+1)]
                #             folium.PolyLine(
                #                 coords,
                #                 color='orange',
                #                 weight=4,
                #                 opacity=0.8,
                #                 popup=f"Virage: {virage}"
                #             ).add_to(m)
                    
                #     # Tracer toutes les lignes droites en cyan
                #     for lignes in stats_lignes_droites:
                #         idx_start = lignes["idx_start_gps"]
                #         idx_end = lignes["idx_end_gps"]
                #         coords = [loc_filtre[i] for i in range(idx_start, idx_end+1)]
                #         folium.PolyLine(
                #             coords,
                #             color='cyan',
                #             weight=4,
                #             opacity=0.8,
                #             popup="Ligne droite"
                #         ).add_to(m)
                    
                    
                    # Construire un nom de fichier clair à partir de la date du premier virage analysé
                    # if tableaux_virages:
                    #     # Prendre le premier virage dans le dict
                    #     premiere_liste = next(iter(tableaux_virages.values()))
                    #     if premiere_liste:
                    #         date_str = premiere_liste[0]["date"].strftime("%Y-%m-%d")
                    #     else:
                    #         date_str = "unknown_date"
                    # else:
                    #     date_str = "unknown_date"
                    
                    # nom_fichier_html = f"carte_virages_{trajet}_{sens}_{date_str}.html"
                    # chemin_html = f"C:/Users/sofian.berkane/Downloads/Soso/Code/carte/test/{nom_fichier_html}
                    # m.save(chemin_html)
                    # print(f"✅ Carte sauvegardée : {chemin_html}")
                
            except Exception as e:
                print(f"❌ Erreur lors du traitement de {capteur.name} : {e}")
        
    # Extraire uniquement les clusters récurrents (≥ 3)
    anomalies_recurrentes = {
        freq: [c for c in clusters if c["count"] >= recurence]
        for freq, clusters in anomaly_clusters_by_freq.items()
    }

    # === 🗺️ Carte Folium ===
    # Trouver un centre raisonnable (premier cluster trouvé)
    any_cluster = next((c for clusters in anomalies_recurrentes.values() for c in clusters), None)
    center = any_cluster["position"] if any_cluster else loc_interp[0]  # fallback Paris

    # m = folium.Map(location=center, zoom_start=14)

    # # Couleurs simples pour les micros (tu peux adapter la palette)
    # colors = [
    #     "red", "blue", "green", "purple", "orange", "darkred",
    #     "lightblue", "darkgreen", "cadetblue", "darkpurple"
    # ]
    # freq_colors = {freq: colors[i % len(colors)] for i, freq in enumerate(anomalies_recurrentes)}

    # # Ajout des cercles
    # for freq, clusters in anomalies_recurrentes.items():
    #     for cluster in clusters:
    #         folium.Circle(
    #             location=cluster["position"],
    #             radius=5,
    #             color=freq_colors[freq],
    #             fill=True,
    #             fill_opacity=0.6,
    #             popup=f"{freq} - {cluster['count']} fichiers"
    #         ).add_to(m)

    # # Sauvegarde et ouverture
    # output_path = f"./anomalies_{trajet}_{sens}_par_freq.html"
    # m.save(output_path)
    # webbrowser.open(f"file://{os.path.abspath(output_path)}")

    return tableaux_globaux, lignes_droites_global, anomalies_recurrentes, depassements_par_capteur

virages, ligne_droites, anomalies_recurrentes, depassement_capteur = analyse_multi("ligne_4", "sens_1")

# # Liste pour stocker les lignes
# lignes = []

# # Parcours de chaque virage 
# for nom_virage, mesures_par_jour in virages.items():
#     for mesure in mesures_par_jour:
#         ligne = {"virage": nom_virage}
#         ligne.update(mesure)  # ajoute tous les champs du jour
#         lignes.append(ligne)

# # Conversion en DataFrame
# df = pd.DataFrame(lignes)

# # Export CSV
# df.to_csv("virages_par_jour.csv", index=False)