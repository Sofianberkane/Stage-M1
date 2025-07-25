# 📊 Analyse de Données GPS et Capteurs pour Tramways

Ce projet Python permet de traiter, analyser et visualiser des données issues de capteurs embarqués (accéléromètres et microphones) ainsi que de traces GPS, collectées lors de trajets en tramway dans la métropole de Lyon. L'objectif principal est de détecter et caractériser les comportements dynamiques du tram (virages, arrêts, anomalies sonores/accélérations).

---

## 📁 Structure du projet

├── gps_utils.py # Outils de géolocalisation (conversion, distance, parsing)
├── rec_data_gps.py # Extraction des positions, vitesses, arrêts depuis les fichiers GPS
├── rec_data_capt.py # Analyse des fichiers capteurs (microphones, accéléros)
├── recuperer_fichiers.py # Association automatique des fichiers GPS/capteurs par date
├── trier_parcours.py # Classification automatique des trajets bruts selon des parcours de référence
├── trier_les_chemin.py # Découpage des trajets complets en segments par sens (aller/retour)
├── tracer_tout_dans_un_dossier.py # Visualisation automatique des trajets sous forme de cartes HTML
├── analyser_multi_jours.py # Pipeline d'analyse multi-jours de virages, lignes droites et anomalies

## ⚙️ Fonctionnalités principales

### 🔍 Traitement des données GPS
- Extraction des coordonnées GPS à partir de trames `$GNRMC`
- Filtrage des points stationnaires
- Correction des points à vitesse nulle par interpolation
- Calcul des vitesses

### 📡 Analyse des fichiers capteurs
- Lecture et nettoyage des fichiers capteurs (format tabulé)
- Synchronisation temporelle entre GPS et capteurs
- Calcul d'indicateurs par virage et ligne droite (accélérations, niveaux sonores)
- Détection d’anomalies sonores par écart à une tendance théorique

### 🧠 Segmentation et classification
- Classement automatique des trajets bruts en fonction de parcours de référence (`trier_parcours.py`)
- Segmentation des trajets en `sens_1` et `sens_2` par détection des terminus (`trier_les_chemin.py`)

### 🗺️ Visualisation
- Cartes interactives des trajets générées avec Folium (`tracer_tout_dans_un_dossier.py`)
- Marquage des arrêts, virages, et anomalies

---

## 🔄 Pipeline de traitement recommandé

1. **Classification automatique des trajets bruts**  
   `python trier_parcours.py`

2. **Segmentation des trajets complets en sens aller/retour**  
   `python trier_les_chemin.py`

3. **Association des fichiers capteurs aux trajets GPS**  
   (appelé automatiquement par les scripts d’analyse)

4. **Analyse complète multi-jours d’un trajet et sens donné**  
   Modifier et exécuter :  
   `python analyser_multi_jours.py`

---

## 📌 Dépendances

- `numpy`
- `pandas`
- `matplotlib`
- `folium`
- `seaborn`
- `pynmeagps`
- `scikit-learn`
- `geopy`

Installe-les avec :

```bash
pip install numpy pandas matplotlib folium seaborn pynmeagps scikit-learn geopy
