import math
import pandas as pd
from datetime import datetime

class ETCalculator:
    def __init__(self):
        self.crop_coefficients = {
            'corn': {'initial': 0.3, 'mid': 1.2, 'late': 0.6},
            'wheat': {'initial': 0.3, 'mid': 1.15, 'late': 0.4},
            'soybean': {'initial': 0.4, 'mid': 1.15, 'late': 0.5},
            'cotton': {'initial': 0.35, 'mid': 1.2, 'late': 0.7},
            'alfalfa': {'initial': 0.4, 'mid': 1.2, 'late': 1.1}
        }
        
        self.crop_root_depths = {
            'corn': 1.2,
            'wheat': 1.0,
            'soybean': 0.8,
            'cotton': 1.5,
            'alfalfa': 1.2
        }
    
    def get_crop_coefficient(self, crop_type, days_since_planting, growing_season_days=120):
        """
        Get crop coefficient based on growth stage
        """
        if crop_type not in self.crop_coefficients:
            return 1.0  # Default value
        
        growth_stage = days_since_planting / growing_season_days
        
        if growth_stage < 0.2:  # Initial stage
            return self.crop_coefficients[crop_type]['initial']
        elif growth_stage < 0.7:  # Mid-season stage
            return self.crop_coefficients[crop_type]['mid']
        else:  # Late season stage
            return self.crop_coefficients[crop_type]['late']
    
    def get_crop_root_depth(self, crop_type):
        """Get typical root depth for crop"""
        return self.crop_root_depths.get(crop_type, 1.0)
    
    def calculate_et0(self, temperature, humidity, wind_speed, solar_radiation, latitude, day_of_year):
        """
        Calculate Reference Evapotranspiration (ET0) using FAO Penman-Monteith equation
        """
        # Constants
        G_SC = 0.0820  # Solar constant (MJ m-2 min-1)
        ALBEDO = 0.23  # Albedo for grass reference crop
        
        # 1. Saturation vapor pressure (es)
        es = 0.6108 * math.exp((17.27 * temperature) / (temperature + 237.3))
        
        # 2. Actual vapor pressure (ea)
        ea = (humidity / 100) * es
        
        # 3. Slope of vapor pressure curve (Δ)
        delta = (4098 * es) / ((temperature + 237.3) ** 2)
        
        # 4. Psychrometric constant (γ)
        gamma = 0.665 * 0.001  # Assuming atmospheric pressure ~101.3 kPa
        
        # 5. Extraterrestrial radiation (Ra)
        dr = 1 + 0.033 * math.cos((2 * math.pi / 365) * day_of_year)
        delta_rad = 0.409 * math.sin((2 * math.pi / 365) * day_of_year - 1.39)
        phi = (math.pi / 180) * latitude
        ws = math.acos(-math.tan(phi) * math.tan(delta_rad))
        Ra = (24 * 60 / math.pi) * G_SC * dr * (
            ws * math.sin(phi) * math.sin(delta_rad) + 
            math.cos(phi) * math.cos(delta_rad) * math.sin(ws)
        )
        
        # 6. Net solar radiation (Rns)
        Rns = (1 - ALBEDO) * solar_radiation
        
        # 7. Net outgoing longwave radiation (Rnl)
        sigma = 4.903e-9  # Stefan-Boltzmann constant
        Rnl = sigma * (((temperature + 273.16) ** 4) / 2) * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * (solar_radiation / Ra) - 0.35)
        
        # 8. Net radiation (Rn)
        Rn = Rns - Rnl
        
        # 9. Soil heat flux (G) - assumed 0 for daily calculations
        G = 0
        
        # 10. FAO Penman-Monteith equation
        et0 = (0.408 * delta * (Rn - G) + 
               gamma * (900 / (temperature + 273)) * wind_speed * (es - ea)) / (
               delta + gamma * (1 + 0.34 * wind_speed))
        
        return max(et0, 0)  # ET0 cannot be negative
    
    def calculate_crop_water_demand(self, et0, crop_type, days_since_planting):
        """Calculate crop water demand considering growth stage"""
        kc = self.get_crop_coefficient(crop_type, days_since_planting)
        return et0 * kc

# Example usage
if __name__ == "__main__":
    from nasa_power import NASAPowerClient

    # Example: New York area
    latitude = 40.5
    longitude = -74.5

    # Fetch weather data for the last 7 days
    nasa_client = NASAPowerClient()
    import datetime
    today = datetime.datetime.now()
    start_date = (today - datetime.timedelta(days=7)).strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')
    weather_df = nasa_client.get_weather_data(latitude, longitude, start_date, end_date)

    calculator = ETCalculator()
    if weather_df is not None and not weather_df.empty:
        for _, row in weather_df.iterrows():
            date = row['date']
            temp = row['temperature']
            humidity = row['relative_humidity']
            wind_speed = row['wind_speed']
            solar_rad = row['solar_radiation']
            # Calculate day of year
            day_of_year = datetime.datetime.strptime(date, '%Y-%m-%d').timetuple().tm_yday
            et0 = calculator.calculate_et0(temp, humidity, wind_speed, solar_rad, latitude, day_of_year)
            print(f"{date}: ET0 = {et0:.2f} mm/day")
    else:
        print("No weather data available from NASA POWER for the given location and dates.")