import os
import re
from pathlib import Path

# Dossiers de données
DOSSIER_CAPTEUR = Path(r"C:\Users\sofian.berkane\Downloads\Soso\Code\data\Recup_DATA_AE2T")
DOSSIER_RESULTATS = Path(r"C:\Users\sofian.berkane\Downloads\Soso\Code\data\fichiers_tram\resultats")

def convertir_date_en_entier(nom_fichier):
    """Transforme une date de nom de fichier en entier ex: 2025_04_02_14_07_31 → 20250402140731"""
    match = re.search(r"(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})", nom_fichier)
    if not match:
        return None
    return int("".join(match.groups()))

def trouver_fichier_capteur_associe(val_gps, fichiers_capteur, seuil=1200):
    """Renvoie la liste des fichiers capteurs dont la date est proche (≤ seuil en secondes)"""
    associes = []
    for cap in fichiers_capteur:
        val_cap = convertir_date_en_entier(cap.name)
        if val_cap and abs(val_cap - val_gps) <= seuil:
            associes.append(cap)
    return associes

def charger_groupes_par_trajet_et_sens(nom_trajet, sens):
    dossier_trajet = DOSSIER_RESULTATS / nom_trajet / sens
    if not dossier_trajet.exists():
        print(f"❌ Le dossier '{dossier_trajet}' n'existe pas.")
        return []

    fichiers_gps = list(dossier_trajet.glob("*.txt"))
    fichiers_capteur = list(DOSSIER_CAPTEUR.glob("ACCELERO_MICRO_*.txt"))

    if not fichiers_gps:
        print("❗ Aucun fichier GPS trouvé dans ce trajet/sens.")
        return []

    groupes = []
    for gps in fichiers_gps:
        val_gps = convertir_date_en_entier(gps.name)
        capteurs_associes = trouver_fichier_capteur_associe(val_gps, fichiers_capteur)
        
        if capteurs_associes:  # ✅ On garde uniquement si un capteur est trouvé
            groupes.append((gps, capteurs_associes))

    if not groupes:
        print("❗ Aucun fichier GPS associé à un fichier capteur.")
        return []

    for i, (gps, capteurs) in enumerate(groupes):
        print(f"\n📁 Segment GPS {i+1}")
        print(f"   GPS : {gps.name}")
        print(f"   {len(capteurs)} capteur(s) associé(s) :")
        for cap in capteurs:
            print(f"      - {cap.name}")

    return groupes

# ========================
# 🧪 Exemple d’utilisation :
# ========================

# if __name__ == "__main__":
#     groupes = charger_groupes_par_trajet_et_sens("Saint_Priest_to_Confluence", "sens_1")
#     gps_path, capteurs_list = groupes[0]
#     print(type(gps_path))

# # # # Accès :
# # # gps_path, capteurs_list = groupes[0]

# print(groupes)

