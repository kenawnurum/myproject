import requests
import pandas as pd
from datetime import datetime, timedelta
import config

class NASAPowerClient:
    def __init__(self):
        self.base_url = config.NASA_POWER_BASE_URL
    
    def get_weather_data(self, latitude, longitude, start_date=None, end_date=None):
        """
        Fetch weather data from NASA POWER API
        """
        # Ensure we don't request future dates
        today = datetime.now()
        if end_date is None:
            end_date = today.strftime('%Y%m%d')
        else:
            end_date_obj = datetime.strptime(end_date, '%Y%m%d')
            if end_date_obj > today:
                end_date = today.strftime('%Y%m%d')
        
        if start_date is None:
            start_date = (today - timedelta(days=30)).strftime('%Y%m%d')
        else:
            start_date_obj = datetime.strptime(start_date, '%Y%m%d')
            if start_date_obj > today:
                start_date = (today - timedelta(days=30)).strftime('%Y%m%d')
        
        print(f"Fetching data from {start_date} to {end_date}")
        
        params = {
            'parameters': config.NASA_PARAMETERS,
            'community': config.COMMUNITY,
            'longitude': longitude,
            'latitude': latitude,
            'start': start_date,
            'end': end_date,
            'format': config.FORMAT
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            print("NASA POWER API URL:", response.url)
            print("Status code:", response.status_code)
            print("Response text:", response.text[:500])  # Print first 500 chars for inspection
            response.raise_for_status()
            try:
                print("Response JSON:", response.json())
            except Exception as json_err:
                print("Could not parse JSON:", json_err)
            return self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NASA POWER data: {e}")
            return None
    
    def _parse_response(self, data):
        """
        Parse NASA POWER API response into structured format
        """
        if 'properties' not in data or 'parameter' not in data['properties']:
            print("No parameters found in response")
            print("Full response:", data)
            return None

        parameters = data['properties']['parameter']
        available_params = list(parameters.keys())
        print(f"Available parameters: {available_params}")

        if 'T2M' not in parameters:
            print("Temperature data (T2M) not available")
            print("Full response:", data)
            return None
        
        dates = list(parameters['T2M'].keys())
        print(f"Found {len(dates)} days of data")
        
        weather_data = []
        valid_days = 0
        
        for date in dates:
            try:
                # Pick corrected precipitation if available
                precip_param = 'PRECTOTCORR' if 'PRECTOTCORR' in parameters else 'PRECTOT'

                # Check required parameters
                missing = []
                for param in ['T2M', 'RH2M', 'WS2M', 'ALLSKY_SFC_SW_DWN', precip_param]:
                    if param not in parameters or date not in parameters[param]:
                        missing.append(param)

                if missing:
                    print(f"Skipping date {date} due to missing parameters: {missing}")
                    continue

                # Precipitation
                precipitation = parameters[precip_param].get(date, 0.0)
                if precipitation is None or not isinstance(precipitation, (int, float)):
                    print(f"Invalid precipitation value for {date}, setting to 0")
                    precipitation = 0.0

                # Clamp temperature [-50, 60]
                temperature = parameters['T2M'][date]
                if temperature < -50:
                    print(f"Clamping temperature {temperature} to -50 for date {date}")
                    temperature = -50
                elif temperature > 60:
                    print(f"Clamping temperature {temperature} to 60 for date {date}")
                    temperature = 60

                daily_data = {
                    'date': datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                    'temperature': temperature,
                    'relative_humidity': parameters['RH2M'][date],
                    'wind_speed': parameters['WS2M'][date],
                    'solar_radiation': parameters['ALLSKY_SFC_SW_DWN'][date],
                    'precipitation': precipitation
                }
                weather_data.append(daily_data)
                valid_days += 1

            except (KeyError, ValueError) as e:
                print(f"Error parsing data for date {date}: {e}")
                continue
        
        print(f"Successfully parsed {valid_days} days of data")
        
        if valid_days == 0:
            return None
            
        return pd.DataFrame(weather_data)

# Test function
def test_nasa_power():
    """Test the NASA POWER client with known good coordinates"""
    client = NASAPowerClient()
    
    # Test with different locations
    test_locations = [
        (40.5, -74.5),  # New York area
        (39.7, -105.0), # Colorado
        (34.0, -118.0), # Los Angeles
    ]
    
    for lat, lon in test_locations:
        print(f"\nTesting coordinates: {lat}, {lon}")
        data = client.get_weather_data(lat, lon)
        if data is not None and not data.empty:
            print(f"Success! Retrieved {len(data)} days of data")
            print(data.head())
            return data
        else:
            print("Failed to retrieve data")
    
    return None

if __name__ == "__main__":
    test_nasa_power()
