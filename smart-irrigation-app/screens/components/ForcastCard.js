// components/ForecastCard.js
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function ForecastCard({ data }) {
  const {
    date,
    temperature,
    precipitation,
    et0,
    crop_kc,
    crop_water_demand,
    soil_moisture_deficit,
    soil_moisture_percent,
    irrigation_needed,
    predicted_irrigation_mm
  } = data;

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <Text style={styles.date}>{date}</Text>
        <Text style={[styles.badge, { backgroundColor: irrigation_needed ? '#f28b82' : '#ccff90' }]}>
          {irrigation_needed ? 'IRRIGATE' : 'NO IRRIGATION'}
        </Text>
      </View>

      <Text>Temp: {temperature} °C  •  Precip: {precipitation} mm</Text>
      <Text>ET₀: {et0} mm  •  Kc: {crop_kc}  •  Demand: {crop_water_demand} mm</Text>
      <Text>Soil deficit: {soil_moisture_deficit} mm ({soil_moisture_percent}%)</Text>
      <Text>Suggested irrigation: {predicted_irrigation_mm} mm</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#fff',
    marginTop: 10,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    elevation: 1
  },
  date: { fontWeight: '700', fontSize: 16 },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6, color: '#000', fontWeight: '600' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }
});
