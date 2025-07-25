import os
import numpy as np
from pynmeagps import NMEAReader
import folium
# from geopy.distance import geodesic
from datetime import datetime
os.chdir("C:/Users/sofian.berkane/Downloads/Soso/Code/data")


def  recup_temps_pos(path):
    fichier = open(path, 'r')
    contenu=fichier.read().splitlines()
    fichier.close()
    
    
    donnee=[]
    temps=[]
    
    for i in range(0,len(contenu)-1):
    	ligne=contenu[i].split(' ')
    	if(ligne!=([('')])):
    		t = ligne[1]
    		temps.append(t)		
    		donnee.append(ligne[3])
    
    

    spd_data=[]
    loc=[]
    date = []
    
    for i in range(0, len(donnee)):
        msg = NMEAReader.parse(donnee[i])
        if msg.identity == "GNRMC":
            if (msg.lat != '') and (msg.lon != ''):
                date.append(temps[i])
                if msg.spd!= '':
                    spd_data.append(float(msg.spd)*1.852)
                else:
                    spd_data.append(0)
                current_point = (msg.lat, msg.lon)
                loc.append(current_point)
        
    
                               
    spd_mini = 0.5
    loc_corrected = []
    i = 0
    while i < len(loc):
        if spd_data[i] >= spd_mini:
            loc_corrected.append(loc[i])
            i += 1
        else:
            if len(loc_corrected) > 0:
                point_before = loc_corrected[-1]
            else:
                point_before = loc[i]
            
            j = i
            while j < len(loc) and spd_data[j] < spd_mini:
                j += 1
            
            if j < len(loc):
                point_after = loc[j]
            else:
                point_after = loc[-1]
            
            n_points = j - i
            
            lat_start, lon_start = point_before
            lat_end, lon_end = point_after
            
            for k in range(n_points):
                ratio = k / (n_points - 1) if n_points > 1 else 0
                lat_new = lat_start + ratio * (lat_end - lat_start)
                lon_new = lon_start + ratio * (lon_end - lon_start)
                loc_corrected.append((lat_new, lon_new))
            i = j
            
    
                    
        
    # créer la map puis tracer le trajet en rouge
    # m = folium.Map(location=(loc_corrected[0]), tiles="cartodb positron")
    # folium.PolyLine(loc_corrected,color='red',weight=2,opacity=0.8).add_to(m)
    
    
    time_stop = []
    idx_stop = []
    
    for i in range(0,len(spd_data)):
        if spd_data[i]<0.5:
            time_stop.append(date[i])
            idx_stop.append(i)
            # folium.CircleMarker(location=(loc_corrected[i]),radius=3, color='blue',fill=True,
            #                      fill_color='blue',fill_opacity=0.8).add_to(m)

    
    
    # m.save("C:/Users/sofian.berkane/Downloads/Soso/Code/carte/carte_avec_arret.html")
    return date,  time_stop, idx_stop, loc_corrected, spd_data
