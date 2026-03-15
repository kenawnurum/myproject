import pandas as pd
import numpy as np

class SoilProperties:
    def __init__(self):
        self.soil_types = self._initialize_soil_types()
    
    def _initialize_soil_types(self):
        """Define soil properties for different soil types"""
        return {
            'sand': {
                'field_capacity': 0.10,  # m³/m³
                'wilting_point': 0.03,   # m³/m³
                'saturation': 0.45,      # m³/m³
                'k_sat': 360.0,          # cm/day (saturated hydraulic conductivity)
                'bulk_density': 1.6,     # g/cm³
                'available_water': 0.07   # m³/m³
            },
            'loamy_sand': {
                'field_capacity': 0.15,
                'wilting_point': 0.05,
                'saturation': 0.40,
                'k_sat': 120.0,
                'bulk_density': 1.55,
                'available_water': 0.10
            },
            'sandy_loam': {
                'field_capacity': 0.20,
                'wilting_point': 0.08,
                'saturation': 0.45,
                'k_sat': 45.0,
                'bulk_density': 1.5,
                'available_water': 0.12
            },
            'loam': {
                'field_capacity': 0.28,
                'wilting_point': 0.12,
                'saturation': 0.50,
                'k_sat': 25.0,
                'bulk_density': 1.4,
                'available_water': 0.16
            },
            'silt_loam': {
                'field_capacity': 0.32,
                'wilting_point': 0.14,
                'saturation': 0.52,
                'k_sat': 15.0,
                'bulk_density': 1.35,
                'available_water': 0.18
            },
            'clay_loam': {
                'field_capacity': 0.35,
                'wilting_point': 0.20,
                'saturation': 0.55,
                'k_sat': 8.0,
                'bulk_density': 1.3,
                'available_water': 0.15
            },
            'clay': {
                'field_capacity': 0.40,
                'wilting_point': 0.25,
                'saturation': 0.60,
                'k_sat': 3.0,
                'bulk_density': 1.25,
                'available_water': 0.15
            }
        }
    
    def get_soil_properties(self, soil_type, root_depth=1.0):
        """
        Get soil properties for a given soil type and root depth
        
        Args:
            soil_type (str): Type of soil
            root_depth (float): Root depth in meters
        
        Returns:
            dict: Soil properties including calculated values
        """
        if soil_type not in self.soil_types:
            soil_type = 'loam'  # Default to loam
        
        props = self.soil_types[soil_type].copy()
        
        # Calculate derived properties
        props['total_available_water'] = props['available_water'] * root_depth * 1000  # mm
        props['readily_available_water'] = props['total_available_water'] * 0.65  # mm
        props['root_depth'] = root_depth
        
        return props
    
    def calculate_soil_moisture_limits(self, soil_type, root_depth=1.0, crop_type=None, days_since_planting=None):
        """
        Calculate soil moisture limits for irrigation scheduling, including crop stage coefficient
        """
        props = self.get_soil_properties(soil_type, root_depth)

        # Calculate management allowed depletion (MAD)
        mad_fraction = 0.55  # 55% depletion allowed
        mad_limit = props['total_available_water'] * mad_fraction

        # Add crop coefficient for current stage if crop_type and days_since_planting are provided
        crop_coefficient = None
        crop_stage = None
        if crop_type is not None and days_since_planting is not None:
            try:
                from et_calculator import ETCalculator
                et_calc = ETCalculator()
                crop_coefficient = et_calc.get_crop_coefficient(crop_type, days_since_planting)
                # Determine stage name
                growth_stage = days_since_planting / 120
                if growth_stage < 0.2:
                    crop_stage = "initial"
                elif growth_stage < 0.7:
                    crop_stage = "mid"
                else:
                    crop_stage = "late"
            except Exception as e:
                crop_coefficient = None
                crop_stage = None

        limits = {
            'field_capacity_mm': props['field_capacity'] * root_depth * 1000,
            'wilting_point_mm': props['wilting_point'] * root_depth * 1000,
            'total_available_water_mm': props['total_available_water'],
            'readily_available_water_mm': props['readily_available_water'],
            'mad_limit_mm': mad_limit,
            'irrigation_threshold_mm': props['total_available_water'] - mad_limit
        }
        if crop_coefficient is not None:
            limits['crop_coefficient'] = crop_coefficient
            limits['crop_stage'] = crop_stage

        return limits

# Example usage
if __name__ == "__main__":
    soil = SoilProperties()
    for soil_type in soil.soil_types.keys():
        props = soil.get_soil_properties(soil_type, 1.2)
        print(f"{soil_type.capitalize()} soil properties:", props)