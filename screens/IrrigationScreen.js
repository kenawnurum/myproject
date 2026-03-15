// screens/IrrigationScreen.js
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, ScrollView, StyleSheet, Alert, ActivityIndicator, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import axios from 'axios';
import ForecastCard from '../components/ForecastCard';
import * as Location from 'expo-location';
import { Button } from 'react-native-paper';

/*
  IMPORTANT:
  - Replace BACKEND_BASE_URL below with your Flask server URL.
  - If testing locally: use your machine IP (e.g. http://192.168.1.5:5000)
  - Or use ngrok to expose local server: https://<your-id>.ngrok.io
*/
const BACKEND_BASE_URL = 'http://192.168.1.100:5000'; // <<---- set this to your server or ngrok

export default function IrrigationScreen() {
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [cropType, setCropType] = useState('maize');
  const [soilType, setSoilType] = useState('loam');
  const [daysSincePlanting, setDaysSincePlanting] = useState('60');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [soilProps, setSoilProps] = useState(null);

  useEffect(() => {
    // Try to get device location on mount
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status === 'granted') {
          const loc = await Location.getCurrentPositionAsync({});
          setLatitude(String(loc.coords.latitude));
          setLongitude(String(loc.coords.longitude));
        }
      } catch (e) {
        console.log('Location permission error:', e);
      }
    })();
  }, []);

  const callBackend = async () => {
    // Validate
    if (!latitude || !longitude) {
      Alert.alert('Missing location', 'Please enter latitude and longitude or allow location permissions.');
      return;
    }
    setLoading(true);
    setResults([]);
    setSoilProps(null);

    try {
      const payload = {
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        crop_type: cropType,
        soil_type: soilType,
        days_since_planting: parseInt(daysSincePlanting || '60', 10)
      };

      const resp = await axios.post(`${BACKEND_BASE_URL}/get_irrigation_data`, payload, { timeout: 30000 });

      if (resp.data && resp.data.success) {
        setResults(resp.data.data || []);
        setSoilProps(resp.data.soil_properties || {});
      } else {
        Alert.alert('Server error', resp.data?.error || 'Unknown response from server');
      }
    } catch (err) {
      console.log('API error', err?.message || err);
      Alert.alert('Request failed', 'Could not reach the server. Check your BACKEND_BASE_URL and CORS settings.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Smart Irrigation</Text>

        <TextInput style={styles.input} placeholder="Latitude" keyboardType="numeric" value={latitude} onChangeText={setLatitude} />
        <TextInput style={styles.input} placeholder="Longitude" keyboardType="numeric" value={longitude} onChangeText={setLongitude} />
        <TextInput style={styles.input} placeholder="Crop Type (e.g., maize)" value={cropType} onChangeText={setCropType} />
        <TextInput style={styles.input} placeholder="Soil Type (e.g., loam)" value={soilType} onChangeText={setSoilType} />
        <TextInput style={styles.input} placeholder="Days since planting" keyboardType="numeric" value={daysSincePlanting} onChangeText={setDaysSincePlanting} />

        <Button mode="contained" onPress={callBackend} disabled={loading} style={{ marginVertical: 10 }}>
          {loading ? 'Loading...' : 'Get Forecast'}
        </Button>

        {loading && <ActivityIndicator size="large" />}

        {soilProps && (
          <View style={styles.soilBox}>
            <Text style={{ fontWeight: 'bold' }}>Soil properties</Text>
            <Text>TAW (mm): {soilProps.total_available_water_mm}</Text>
            <Text>Field capacity (mm): {soilProps.field_capacity_mm}</Text>
            <Text>Irrigation threshold (mm): {soilProps.irrigation_threshold_mm}</Text>
          </View>
        )}

        <View style={{ width: '100%' }}>
          {results.length === 0 && !loading ? <Text style={{ textAlign: 'center', marginTop: 20 }}>No forecast yet.</Text> : null}
          {results.map((day, idx) => (
            <ForecastCard key={idx} data={day} />
          ))}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    alignItems: 'center',
    paddingBottom: 60
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 12
  },
  input: {
    width: '100%',
    padding: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    marginVertical: 6,
    borderRadius: 6
  },
  soilBox: {
    width: '100%',
    padding: 12,
    backgroundColor: '#f4f4f8',
    borderRadius: 8,
    marginTop: 12
  }
});
