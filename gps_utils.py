from math import radians, cos, sin, asin, sqrt

def convert_to_decimal_degrees(raw, direction):
    if not raw:
        return None
    degrees = int(float(raw) / 100)
    minutes = float(raw) - degrees * 100
    decimal = degrees + minutes / 60
    if direction in ["S", "W"]:
        decimal = -decimal
    return round(decimal, 6)

def parse_gnrmc_line(line):
    if "$GNRMC" not in line:
        return None
    try:
        parts = line.split(",")
        if len(parts) < 7:
            return None
        lat = convert_to_decimal_degrees(parts[3], parts[4])
        lon = convert_to_decimal_degrees(parts[5], parts[6])
        return (lat, lon) if lat and lon else None
    except:
        return None

def haversine_km(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # rayon terrestre en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))

