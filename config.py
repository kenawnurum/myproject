import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
latitude = 9.03
longitude = 38.74
elevation_m = 2355 # Approximate elevation for Addis Ababa in meters
import requests, json, datetime
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=365)
# NASA POWER API Configuration
NASA_POWER_BASE_URL = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN,WS2M,RH2M&community=AG&longitude={longitude}&latitude={latitude}&start={start_date.strftime('%Y%m%d')}&end={end_date.strftime('%Y%m%d')}&format=JSON"

NASA_PARAMETERS = "T2M,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOT"
COMMUNITY = "AG"
FORMAT = "JSON"

# App Configuration
DEBUG = True
PORT = 5000