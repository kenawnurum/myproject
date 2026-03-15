import React, { useState } from 'react';
import { View, Text, Button, ScrollView, StyleSheet, ActivityIndicator, Platform } from 'react-native';

export default function IrrigationScreen() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Update the backend URL based on environment
  const backendURL = Platform.OS === 'android'
    ? 'http://10.0.2.2:5000/get_irrigation_data' // Android emulator
    : 'http://10.42.81.130:5000/get_irrigation_data'; // Real device / iOS simulator

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetch(backendURL);
      const text = await response.text(); // Read raw response
      console.log('Raw response:', text);

      // Try parsing JSON
      let result;
      try {
        result = JSON.parse(text);
      } catch (jsonError) {
        console.error('Failed to parse JSON:', jsonError);
        alert('Backend did not return valid JSON.');
        return;
      }

      setData(result);
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

      <Button title={loading ? "Loading..." : "Get Irrigation Data"} onPress={fetchData} disabled={loading} />

      {loading && <ActivityIndicator size="large" color="#00aa00" style={{ marginTop: 20 }} />}

      {data && (
        <View style={styles.card}>
          <Text style={styles.result}>Next Irrigation: {data.next_irrigation}</Text>
          <Text style={styles.result}>Water Amount: {data.water_amount}</Text>
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
