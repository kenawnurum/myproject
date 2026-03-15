import React, { useState } from 'react';
import { View, Text, Button, ScrollView, StyleSheet, ActivityIndicator, Platform } from 'react-native';

export default function IrrigationScreen() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Backend URL (adjust for emulator or real device)
  const backendURL = Platform.OS === 'android'
    ? 'http://10.0.2.2:5000/get_irrigation_data'
    : 'http://10.42.80.242:5000/get_irrigation_data';

  const fetchData = async () => {
    setLoading(true);

    try {
      // POST request with default input values
      const response = await fetch(backendURL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          latitude: 9.0,
          longitude: 39.7,
          crop_type: 'corn',
          soil_type: 'loam',
          days_since_planting: 60,
          last_irrigation_date: '2025-10-06'
        })
      });

      const text = await response.text(); // Raw response
      console.log('Raw response:', text);

      let result;
      try {
        result = JSON.parse(text); // Parse JSON
      } catch (jsonError) {
        console.error('Failed to parse JSON:', jsonError);
        alert('Backend did not return valid JSON.');
        return;
      }

      if (result.success) {
        setData(result.data[0]); // Show first day’s data as example
      } else {
        alert('Error from backend: ' + (result.error || 'Unknown error'));
      }

    } catch (error) {
      console.error('Fetch error:', error);
      alert('Failed to connect to backend. Check network and IP.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>🌾 Smart Irrigation</Text>

      <Button title={loading ? "Loading..." : "get Irrigation Data"} onPress={fetchData} disabled={loading} />

      {loading && <ActivityIndicator size="large" color="#00aa00" style={{ marginTop: 20 }} />}

      {data && (
        <View style={styles.card}>
          <Text style={styles.result}>Date: {data.date}</Text>
          <Text style={styles.result}>Irrigation Needed: {data.irrigation_needed ? 'Yes' : 'No'}</Text>
          <Text style={styles.result}>Predicted Irrigation (mm): {data.predicted_irrigation_mm}</Text>
          <Text style={styles.result}>Soil Moisture (%): {data.soil_moisture_percent}</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', padding: 20 },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 20 },
  card: { marginTop: 20, padding: 15, backgroundColor: '#f0f0f0', borderRadius: 10, width: '100%' },
  result: { fontSize: 18, marginVertical: 5 },
});
