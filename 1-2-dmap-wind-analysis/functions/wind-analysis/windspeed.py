import json
from decimal import Decimal
from typing import Dict

def lambda_handler(event: dict, context):
    """Handler that filters fields and converts wind speeds from knots to km/h.
    """
    monthly_highs = event  # event is already a dict
    
    result = {}
    
    for month_str, row in monthly_highs.items():
        # Convert wind speeds from knots to km/h and filter fields
        wdsp = float(row["WDSP"]) if row["WDSP"] != "999.9" else 0.0
        # mxspd = float(row["MXSPD"]) if row["MXSPD"] != "999.9" else 0.0
        # gust = float(row["GUST"]) if row["GUST"] != "999.9" else 0.0
        
        result[month_str] = {
            "STATION": row["STATION"],
            "DATE": row["DATE"],
            "LATITUDE": row["LATITUDE"],
            "LONGITUDE": row["LONGITUDE"],
            "ELEVATION": row["ELEVATION"],
            "NAME": row["NAME"],
            "WDSP": f"{wdsp * 1.852:.1f}",
            "MXSPD": row["MXSPD"],
            "GUST": row["GUST"],
            "FRSHTT": row["FRSHTT"]
        }
    
    return result