# data_pipeline.py
import numpy as np
import pandas as pd
import os
import joblib
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Use a non-interactive backend for matplotlib to avoid Tkinter calls when running
# in background threads (prevents "main thread is not in main loop" errors).
import matplotlib
matplotlib.use('Agg')
plt.ioff()

# ML libs
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, classification_report
import xgboost as xgb
from sklearn.impute import SimpleImputer

# TensorFlow for LSTM
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Import your existing classes
from nasa_power import NASAPowerClient
from et_calculator import ETCalculator

class RealDataPipeline:
    def __init__(self):
        self.historical_data = None
        self.training_data = None
        self.models_trained = False
        
    def fetch_training_data(self, lat, lon, years=3):
        """
        Fetch multiple years of real NASA POWER data for training
        """
        print(f"📡 Fetching {years} years of real NASA POWER data...")
        
        client = NASAPowerClient()
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=365 * years)  # Multiple years back
        
        all_data = []
        
        # Fetch data in 1-year chunks to avoid API limits
        for year in range(years):
            chunk_start = start_date + timedelta(days=365 * year)
            chunk_end = chunk_start + timedelta(days=364)
            
            chunk_data = client.get_weather_data(
                lat, lon,
                start_date=chunk_start.strftime('%Y%m%d'),
                end_date=chunk_end.strftime('%Y%m%d')
            )
            
            if chunk_data is not None and len(chunk_data) > 0:
                all_data.append(chunk_data)
                print(f"✅ Year {year+1}: {len(chunk_data)} days")
            else:
                print(f"⚠️ Year {year+1}: No data, using synthetic")
                # Generate synthetic data for missing year
                synthetic = self._generate_synthetic_year(chunk_start, lat, lon)
                all_data.append(synthetic)
        
        # Combine all data
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            combined_data = combined_data.drop_duplicates(subset=['date']).sort_values('date')
            
            # Clean and process
            self.historical_data = self._clean_real_data(combined_data, lat, lon)
            print(f"🎯 Final training dataset: {len(self.historical_data)} days")
            return self.historical_data
        else:
            raise Exception("Could not fetch any training data")
    
    def _clean_real_data(self, df, lat, lon):
        """Clean and enhance real NASA POWER data"""
        # Remove invalid rows
        df = df[df['temperature'].between(-50, 60)]
        df = df[df['precipitation'] >= 0]
        
        # Calculate ET0
        et_calc = ETCalculator()
        et0_list = []
        
        for _, row in df.iterrows():
            try:
                date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
                et0 = et_calc.calculate_et0(
                    temperature=row['temperature'],
                    humidity=row['relative_humidity'],
                    wind_speed=row['wind_speed'],
                    solar_radiation=row['solar_radiation'],
                    latitude=lat,
                    day_of_year=date_obj.timetuple().tm_yday
                )
                et0_list.append(et0)
            except:
                et0_list.append(5.0)  # Default fallback
        
        df['et0'] = et0_list
        
        # Add synthetic irrigation labels (in real scenario, you'd have actual irrigation records)
        df = self._add_irrigation_labels(df)
        
        return df
    
    def _add_irrigation_labels(self, df):
        """Add realistic irrigation labels based on weather patterns"""
        # Simulate irrigation decisions based on soil moisture deficit logic
        df['soil_moisture_deficit'] = 0.0
        df['days_since_rain'] = 0
        df['crop_water_demand'] = df['et0'] * np.random.uniform(0.8, 1.2, len(df))
        
        # Calculate soil moisture deficit (simplified water balance)
        current_deficit = 0
        days_since_rain = 0
        
        for i, row in df.iterrows():
            # Update days since rain
            if row['precipitation'] > 5:
                days_since_rain = 0
            else:
                days_since_rain += 1
            
            # Update soil moisture deficit
            net_water = row['precipitation'] - row['crop_water_demand']
            current_deficit = max(0, current_deficit - net_water)
            current_deficit = min(current_deficit, 100)  # Cap at 100mm
            
            df.at[i, 'soil_moisture_deficit'] = current_deficit
            df.at[i, 'days_since_rain'] = days_since_rain
        
        # Create irrigation labels
        df['irrigation_amount'] = np.where(
            (df['soil_moisture_deficit'] > 40) | (df['days_since_rain'] > 7),
            np.clip(df['soil_moisture_deficit'] * 0.6 + np.random.normal(0, 5), 0, 50),
            0
        )
        
        df['needs_irrigation'] = (df['irrigation_amount'] > 5).astype(int)
        
        return df
    
    def _generate_synthetic_year(self, start_date, lat, lon):
        """Generate realistic synthetic data for a year"""
        dates = []
        temperatures = []
        precipitations = []
        
        current_date = start_date
        for day in range(365):
            dates.append(current_date.strftime('%Y-%m-%d'))
            
            # Seasonal temperature variation
            day_of_year = current_date.timetuple().tm_yday
            base_temp = 15 + 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)  # Seasonal
            
            # Add daily variation
            temperature = base_temp + np.random.normal(0, 3)
            temperatures.append(temperature)
            
            # Seasonal precipitation (more in certain months)
            month = current_date.month
            if month in [6, 7, 8]:  # Summer months - more rain
                precip = np.random.exponential(3)
            else:
                precip = np.random.exponential(1)
            precipitations.append(precip)
            
            current_date += timedelta(days=1)
        
        data = {
            'date': dates,
            'temperature': temperatures,
            'precipitation': precipitations,
            'relative_humidity': np.random.uniform(40, 80, 365),
            'wind_speed': np.random.uniform(1, 4, 365),
            'solar_radiation': np.random.uniform(15, 25, 365)
        }
        
        return pd.DataFrame(data)

class RealTimeForecaster:
    def __init__(self):
        self.lstm_model = None
        self.irrigation_model = None
        self.performance_metrics = {}
        
    def train_on_real_data(self, historical_df, forecast_days=10):
        """
        Train models on real historical data
        """
        print("🤖 Training models on real historical data...")
        
        # 1. Train LSTM for forecasting
        self._train_lstm(historical_df, forecast_days)
        
        # 2. Train irrigation model
        self._train_irrigation_model(historical_df)
        
        # 3. Evaluate models
        self._evaluate_models(historical_df)
        
        self.models_trained = True
        print("✅ All models trained and evaluated")
    
    def _train_lstm(self, df, forecast_days):
        """Train LSTM model for weather forecasting"""
        features = ['temperature', 'precipitation', 'et0', 'solar_radiation']
        
        # Prepare data
        data = df[features].values
        
        # Create sequences
        lookback = 30
        X, y = [], []
        
        for i in range(len(data) - lookback - forecast_days):
            X.append(data[i:i + lookback])
            y.append(data[i + lookback:i + lookback + forecast_days].flatten())
        
        X, y = np.array(X), np.array(y)
        
        if len(X) == 0:
            print("⚠️ Not enough data for LSTM, using fallback")
            return
        
        # Scale data
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
        
        X_scaled = self.scaler_X.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        y_scaled = self.scaler_y.fit_transform(y)
        
        # Build LSTM model
        self.lstm_model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(lookback, len(features))),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(128, activation='relu'),
            Dense(y.shape[1])
        ])
        
        self.lstm_model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        # Train
        X_train, X_val, y_train, y_val = train_test_split(X_scaled, y_scaled, test_size=0.2, random_state=42)
        
        history = self.lstm_model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=50,
            batch_size=32,
            verbose=0,
            callbacks=[EarlyStopping(patience=10, restore_best_weights=True)]
        )
        
        # Store performance
        self.performance_metrics['lstm'] = {
            'train_loss': history.history['loss'][-1],
            'val_loss': history.history['val_loss'][-1],
            'train_mae': history.history['mae'][-1],
            'val_mae': history.history['val_mae'][-1]
        }
    
    def _train_irrigation_model(self, df):
        """Train irrigation prediction model"""
        # Features for irrigation prediction
        feature_cols = [
            'soil_moisture_deficit', 'et0', 'temperature',
            'precipitation', 'days_since_rain', 'crop_water_demand'
        ]
        
        X = df[feature_cols].values
        y_reg = df['irrigation_amount'].values
        y_clf = df['needs_irrigation'].values
        
        # Handle missing values
        imputer = SimpleImputer(strategy='median')
        X = imputer.fit_transform(X)
        
        # Split data
        X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
            X, y_reg, y_clf, test_size=0.2, random_state=42
        )
        
        # Train regression model (irrigation amount)
        self.reg_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.reg_model.fit(X_train, y_reg_train)
        
        # Train classification model (irrigation decision)
        self.clf_model = xgb.XGBClassifier(n_estimators=100, random_state=42)
        self.clf_model.fit(X_train, y_clf_train)
        
        # Store performance
        y_reg_pred = self.reg_model.predict(X_test)
        y_clf_pred = self.clf_model.predict(X_test)
        
        self.performance_metrics['irrigation_regression'] = {
            'mse': mean_squared_error(y_reg_test, y_reg_pred),
            'mae': mean_absolute_error(y_reg_test, y_reg_pred),
            'r2': r2_score(y_reg_test, y_reg_pred)
        }
        
        self.performance_metrics['irrigation_classification'] = {
            'accuracy': accuracy_score(y_clf_test, y_clf_pred)
        }
    
    def _evaluate_models(self, df):
        """Evaluate model performance and create graphs"""
        print("📊 Evaluating model performance...")
        
        # Create evaluation directory
        os.makedirs('nasa_power_irrigation_app/static/performance', exist_ok=True)
        
        # 1. LSTM Performance Plot
        if 'lstm' in self.performance_metrics:
            plt.figure(figsize=(10, 6))
            metrics = self.performance_metrics['lstm']
            labels = ['Train Loss', 'Val Loss', 'Train MAE', 'Val MAE']
            values = [metrics['train_loss'], metrics['val_loss'], metrics['train_mae'], metrics['val_mae']]
            
            plt.bar(labels, values, color=['blue', 'orange', 'green', 'red'])
            plt.title('LSTM Model Performance')
            plt.ylabel('Metric Value')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('nasa_power_irrigation_app/static/performance/lstm_performance.png')
            plt.close()
        
        # 2. Irrigation Model Performance
        plt.figure(figsize=(12, 5))
        
        # Regression metrics
        plt.subplot(1, 2, 1)
        if 'irrigation_regression' in self.performance_metrics:
            metrics = self.performance_metrics['irrigation_regression']
            labels = ['MSE', 'MAE', 'R²']
            values = [metrics['mse'], metrics['mae'], metrics['r2']]
            
            bars = plt.bar(labels, values, color=['red', 'blue', 'green'])
            plt.title('Irrigation Regression Performance')
            plt.ylabel('Metric Value')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                        f'{value:.3f}', ha='center', va='bottom')
        
        # Classification metrics
        plt.subplot(1, 2, 2)
        if 'irrigation_classification' in self.performance_metrics:
            accuracy = self.performance_metrics['irrigation_classification']['accuracy']
            plt.bar(['Accuracy'], [accuracy], color='purple')
            plt.title(f'Classification Accuracy: {accuracy:.3f}')
            plt.ylim(0, 1)
            
            # Add value label
            plt.text(0, accuracy + 0.02, f'{accuracy:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('nasa_power_irrigation_app/static/performance/irrigation_performance.png')
        plt.close()
        
        # 3. Training Data Overview
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.plot(df['date'][-100:], df['temperature'][-100:])  # Last 100 days
        plt.title('Temperature Trend (Last 100 days)')
        #plt.xticks(rotation=45)
        
        plt.subplot(2, 2, 2)
        plt.plot(df['date'][-100:], df['precipitation'][-100:])
        plt.title('Precipitation Trend (Last 100 days)')
        #plt.xticks(rotation=45)
        
        plt.subplot(2, 2, 3)
        plt.plot(df['date'][-100:], df['et0'][-100:])
        plt.title('ET0 Trend (Last 100 days)')
        #plt.xticks(rotation=45)
        
        plt.subplot(2, 2, 4)
        irrigation_days = df['needs_irrigation'].value_counts()
        plt.pie(irrigation_days.values, labels=['No Irrigation', 'Irrigation Needed'], autopct='%1.1f%%')
        plt.title('Irrigation Distribution in Training Data')
        
        plt.tight_layout()
        plt.savefig('nasa_power_irrigation_app/static/performance/training_data_overview.png')
        plt.close()
        
        print("✅ Performance graphs saved to nasa_power_irrigation_app/static/performance/")
    
    def forecast(self, historical_df, forecast_days=10):
        """Generate forecast using trained models"""
        if not self.models_trained:
            raise ValueError("Models not trained. Call train_on_real_data first.")
        
        features = ['temperature', 'precipitation', 'et0', 'solar_radiation']
        
        # Get the most recent sequence for forecasting
        recent_data = historical_df[features].tail(30).values
        
        # Scale and predict
        recent_scaled = self.scaler_X.transform(recent_data)
        recent_scaled = recent_scaled.reshape(1, 30, len(features))
        
        forecast_scaled = self.lstm_model.predict(recent_scaled, verbose=0)
        forecast_values = self.scaler_y.inverse_transform(forecast_scaled)
        
        # Reshape to (forecast_days, features)
        forecast_values = forecast_values[0].reshape(forecast_days, len(features))
        
        # Create forecast DataFrame
        last_date = datetime.strptime(historical_df['date'].iloc[-1], '%Y-%m-%d')
        forecast_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(forecast_days)]
        
        forecast_df = pd.DataFrame(forecast_values, columns=features)
        forecast_df['date'] = forecast_dates
        
        # Predict irrigation for each forecast day
        results = []
        for _, row in forecast_df.iterrows():
            # Create features for irrigation prediction
            features_dict = {
                'soil_moisture_deficit': 35.0,  # Would come from soil model
                'et0': float(row['et0']),
                'temperature': float(row['temperature']),
                'precipitation': float(row['precipitation']),
                'days_since_rain': 5,  # Default
                'crop_water_demand': float(row['et0']) * 1.0  # Simple estimate
            }
            
            # Make predictions
            irrigation_amount = self.reg_model.predict([list(features_dict.values())])[0]
            needs_irrigation = self.clf_model.predict([list(features_dict.values())])[0]
            confidence = np.max(self.clf_model.predict_proba([list(features_dict.values())]))
            
            results.append({
                'date': row['date'],
                'temperature': float(row['temperature']),
                'precipitation_mm': float(row['precipitation']),
                'et0_mm': float(row['et0']),
                'irrigation_amount_mm': max(0, irrigation_amount),
                'needs_irrigation': bool(needs_irrigation),
                'confidence': confidence,
                'recommendation': 'IRRIGATE' if needs_irrigation else 'NO IRRIGATION NEEDED'
            })
        
        return pd.DataFrame(results)

# Global instances
data_pipeline = RealDataPipeline()
forecaster = RealTimeForecaster()

def initialize_ml_models(lat=9.0, lon=39.7):
    """Initialize and train ML models on startup"""
    print("🚀 Initializing ML models with real NASA POWER data...")
    
    try:
        # Fetch real training data
        training_data = data_pipeline.fetch_training_data(lat, lon, years=2)
        
        # Train models
        forecaster.train_on_real_data(training_data, forecast_days=10)
        
        print("✅ ML models initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ ML model initialization failed: {e}")
        return False

# Initialize on import
if __name__ == "__main__":
    initialize_ml_models()