# app.py
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import config
# Import our data pipeline and forecaster
from irrigation_predictor import data_pipeline, forecaster, initialize_ml_models
from soil_properties import SoilProperties
import threading
from flask_cors import CORS
app = Flask(__name__)

# Global variable to store current forecasts
current_forecast = None
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

@app.route('/generate_performance_graphs')
def generate_performance_graphs():
    """Generate and save performance graphs"""
    try:
        # Create performance directory
        os.makedirs('nasa_power_irrigation_app/static/performance', exist_ok=True)
        
        # Generate sample performance data (replace with your actual metrics)
        performance_data = {
            'models': ['FAO-56 Only', 'Random Forest', 'XGBoost', 'LSTM', 'Hybrid Model'],
            'accuracy': [82.3, 87.1, 88.5, 89.2, 94.7],
            'rmse': [1.45, 0.98, 0.87, 0.79, 0.52],
            'water_savings': [15.2, 22.7, 25.3, 28.1, 32.4]
        }
        
        # 1. LSTM Performance Graph
        plt.figure(figsize=(10, 6))
        epochs = list(range(1, 101, 10))
        train_loss = [0.8 * (0.95 ** i) for i in range(10)]
        val_loss = [0.85 * (0.94 ** i) for i in range(10)]
        
        plt.plot(epochs, train_loss, 'b-', label='Training Loss', linewidth=2)
        plt.plot(epochs, val_loss, 'r-', label='Validation Loss', linewidth=2)
        plt.title('LSTM Training Progress', fontsize=16, fontweight='bold')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('nasa_power_irrigation_app/static/performance/lstm_performance.png', 
                   dpi=150, bbox_inches='tight')
        plt.close()
        
        # 2. Model Comparison Graph
        plt.figure(figsize=(12, 6))
        x_pos = np.arange(len(performance_data['models']))
        
        plt.bar(x_pos - 0.2, performance_data['accuracy'], 0.4, 
                label='Accuracy (%)', alpha=0.8, color='#2E8B57')
        plt.bar(x_pos + 0.2, performance_data['water_savings'], 0.4, 
                label='Water Savings (%)', alpha=0.8, color='#4dabf7')
        
        plt.xlabel('Models')
        plt.ylabel('Performance Metrics')
        plt.title('Model Performance Comparison', fontsize=16, fontweight='bold')
        plt.xticks(x_pos, performance_data['models'], rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('nasa_power_irrigation_app/static/performance/irrigation_performance.png', 
                   dpi=150, bbox_inches='tight')
        plt.close()
        
        # 3. Training Data Overview
        plt.figure(figsize=(12, 6))
        
        # Sample training data timeline
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='M')
        data_points = [150, 320, 480, 620, 750, 890, 1020, 1150, 1280, 1420, 1550, 1680]
        accuracy_trend = [75, 78, 82, 85, 87, 88, 90, 91, 92, 93, 94, 94.7]
        
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        color = 'tab:blue'
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Training Data Points', color=color)
        ax1.plot(dates, data_points, color=color, linewidth=2, marker='o')
        ax1.tick_params(axis='y', labelcolor=color)
        
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Model Accuracy (%)', color=color)
        ax2.plot(dates, accuracy_trend, color=color, linewidth=2, marker='s', linestyle='--')
        ax2.tick_params(axis='y', labelcolor=color)
        
        plt.title('Training Data Growth and Model Accuracy Over Time', 
                 fontsize=16, fontweight='bold')
        fig.tight_layout()
        plt.savefig('nasa_power_irrigation_app/static/performance/training_data_overview.png', 
                   dpi=150, bbox_inches='tight')
        plt.close()
        
        return jsonify({'success': True, 'message': 'Performance graphs generated'})
        
    except Exception as e:
        print(f"Error generating performance graphs: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_performance_metrics')
def get_performance_metrics():
    """Get comprehensive model performance metrics"""
    try:
        # Sample metrics - replace with your actual model metrics
        metrics = {
            'lstm': {
                'train_loss': 0.0234,
                'val_loss': 0.0312,
                'train_mae': 0.0456,
                'val_mae': 0.0521,
                'last_epoch': 100
            },
            'irrigation_regression': {
                'mse': 0.467,
                'mae': 0.412,
                'r2': 0.947,
                'rmse': 0.521
            },
            'irrigation_classification': {
                'accuracy': 0.934,
                'precision': 0.921,
                'recall': 0.945,
                'f1_score': 0.933,
                'confusion_matrix': [[45, 5], [3, 47]]  # [[TN, FP], [FN, TP]]
            },
            'overall': {
                'water_savings': 32.4,
                'prediction_accuracy': 94.7,
                'training_completed': '2024-01-15',
                'data_points': 1680
            },
            'feature_importance': {
                'temperature': 0.234,
                'soil_moisture': 0.198,
                'solar_radiation': 0.187,
                'humidity': 0.156,
                'wind_speed': 0.125,
                'precipitation': 0.100
            }
        }
        
        return jsonify({'success': True, 'metrics': metrics})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route('/')
def index():
    """Main page with performance graphs"""
    return render_template('index.html')

@app.route('/performance')
def performance():
    """Display model performance graphs"""
    return render_template('performance.html')
@app.route('/get_soil_types')
def get_soil_types():
    """Return available soil types"""
    soil_types = [
        'sand', 'loamy_sand', 'sandy_loam', 'loam', 
        'silt_loam', 'clay_loam', 'clay'
    ]
    return jsonify({'soil_types': soil_types})
@app.route('/get_performance_graphs')
def get_performance_graphs():
    """API endpoint to get performance graph paths"""
    graphs = {
        'lstm_performance': '/static/performance/lstm_performance.png',
        'irrigation_performance': '/static/performance/irrigation_performance.png',
        'training_data_overview': '/static/performance/training_data_overview.png'
    }
    
    # Check if graphs exist
    for graph_name, graph_path in graphs.items():
        full_path = f'nasa_power_irrigation_app{graph_path}'
        if not os.path.exists(full_path):
            graphs[graph_name] = None
    
    return jsonify(graphs)

@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    """Forecast page with irrigation recommendations"""
    global current_forecast
    
    if request.method == 'POST':
        try:
            data = request.json
            lat = float(data.get('latitude', 9.0))
            lon = float(data.get('longitude', 39.7))
            forecast_days = int(data.get('forecast_days', 10))
            
            # Generate forecast
            if forecaster.models_trained and data_pipeline.historical_data is not None:
                current_forecast = forecaster.forecast(
                    data_pipeline.historical_data, 
                    forecast_days=forecast_days
                )
                
                # Convert to JSON-serializable format
                forecast_json = current_forecast.to_dict('records')

                # Normalize keys expected by frontend
                norm_forecast = []
                for row in forecast_json:
                    # Pick irrigation amount from several possible keys to avoid missing values
                    irrigation_amt = None
                    for k in ('irrigation_amount_mm', 'predicted_irrigation_mm', 'irrigation_amount', 'predicted_irrigation'):
                        if k in row and row.get(k) is not None:
                            irrigation_amt = row.get(k)
                            break
                    if irrigation_amt is None:
                        irrigation_amt = 0.0

                    # precipitation and et0 fallbacks
                    precip_val = None
                    for k in ('precipitation_mm', 'precipitation'):
                        if k in row and row.get(k) is not None:
                            precip_val = row.get(k)
                            break
                    if precip_val is None:
                        precip_val = 0.0

                    et0_val = None
                    for k in ('et0_mm', 'et0'):
                        if k in row and row.get(k) is not None:
                            et0_val = row.get(k)
                            break
                    # default et0 to 0.0 if missing
                    if et0_val is None:
                        et0_val = 0.0

                    norm_row = {
                        'date': row.get('date'),
                        'temperature': float(row.get('temperature', 0.0)),
                        'precipitation_mm': float(precip_val),
                        'et0_mm': float(et0_val),
                        'irrigation_amount_mm': float(irrigation_amt),
                        'needs_irrigation': bool(row.get('needs_irrigation', row.get('irrigation_needed', False))),
                        'recommendation': row.get('recommendation', 'IRRIGATE' if row.get('needs_irrigation', False) else 'NO IRRIGATION NEEDED'),
                        'confidence': float(row.get('confidence', 0.0))
                    }
                    norm_forecast.append(norm_row)
                forecast_json = norm_forecast
                
                return jsonify({
                    'success': True,
                    'forecast': forecast_json,
                    'summary': {
                        'total_days': len(forecast_json),
                        'irrigation_days': sum(1 for day in forecast_json if day['needs_irrigation']),
                        'total_water_mm': sum(day['irrigation_amount_mm'] for day in forecast_json),
                        'avg_confidence': np.mean([day['confidence'] for day in forecast_json])
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Models not trained. Please wait for initialization.'
                })
                
        except Exception as e:
            import traceback
            print("Exception in /forecast POST:", traceback.format_exc())
            # Return a valid JSON response with status code 500
            return (
                jsonify({
                    'success': False,
                    'error': f'Forecast generation failed: {str(e)}'
                }),
                500
            )

    return render_template('forecast.html')

@app.route('/get_irrigation_data', methods=['POST'])
def get_irrigation_data():
    """API endpoint for irrigation data (for frontend JS)"""
    try:
        # 1. Get user input from request
        data = request.get_json(force=True)
        latitude = float(data.get('latitude', 18.37))
        longitude = float(data.get('longitude', 45.76))
        crop_type = data.get('crop_type', 'corn')
        soil_type = data.get('soil_type', 'loam')
        # Optional explicit current deficit in mm
        current_deficit = data.get('current_deficit', None)
        days_since_planting = int(data.get('days_since_planting', 60))
        # Accept last irrigation date (YYYY-MM-DD) or days_since_irrigation
        last_irrigation_date = data.get('last_irrigation_date', None)
        days_since_irrigation = data.get('days_since_irrigation', None)

        # 2. Fetch 1 year of weather data from NASA POWER
        from nasa_power import NASAPowerClient
        from et_calculator import ETCalculator
        nasa_client = NASAPowerClient()
        today = datetime.now()
        start_date = (today - timedelta(days=365)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        weather_df = nasa_client.get_weather_data(latitude, longitude, start_date, end_date)

        if weather_df is None or weather_df.empty:
            return jsonify({
                'success': False,
                'error': 'Could not fetch weather data from NASA POWER.'
            }), 500

        # Clean NASA POWER data: remove rows with -999 or other fill values
        for col in ['temperature', 'relative_humidity', 'wind_speed', 'solar_radiation', 'precipitation']:
            if col in weather_df.columns:
                weather_df = weather_df[weather_df[col] > -900]

        # Use the last 30 days for training the model
        train_df = weather_df.iloc[-33:-3]  # 30 days before the last 3 days
        # Use the last 3 days for prediction (NASA POWER unreliable)
        predict_last3_df = weather_df.iloc[-3:]

        # Use the next 3 days for future prediction (simulate with ML/DL)
        # For demonstration, we'll just copy the last 3 days and shift the date
        predict_next3_df = predict_last3_df.copy()
        predict_next3_df = predict_next3_df.reset_index(drop=True)
        for i in range(3):
            next_date = (datetime.strptime(predict_last3_df.iloc[-1]['date'], '%Y-%m-%d') + timedelta(days=i+1)).strftime('%Y-%m-%d')
            predict_next3_df.at[i, 'date'] = next_date

        # Combine all for results: (train_df is for model training, not shown)
        combined_results = pd.concat([weather_df.iloc[-6:-3], predict_last3_df, predict_next3_df], ignore_index=True)

        # 3. Get soil properties and crop info
        soil_obj = SoilProperties()
        et_calc = ETCalculator()
        root_depth = et_calc.get_crop_root_depth(crop_type)
        soil_props = soil_obj.get_soil_properties(soil_type, root_depth=root_depth)
        soil_limits = soil_obj.calculate_soil_moisture_limits(soil_type, root_depth=root_depth,
                                                             crop_type=crop_type, days_since_planting=days_since_planting)
        crop_info = {
            'root_depth': root_depth,
            'crop_coefficient': et_calc.get_crop_coefficient(crop_type, days_since_planting)
        }

        # Determine initial total_deficit
        if current_deficit is not None:
            total_deficit = float(current_deficit)
        else:
            # Compute days since irrigation if date provided
            if last_irrigation_date:
                try:
                    last_dt = datetime.strptime(last_irrigation_date, '%Y-%m-%d')
                    days_since_irrigation = (today.date() - last_dt.date()).days
                except Exception:
                    days_since_irrigation = None
            if days_since_irrigation is None:
                # fallback
                days_since_irrigation = int(data.get('days_since_irrigation', 7))

            # Estimate current deficit as a fraction of total available water proportional to days since irrigation
            taw = soil_limits.get('total_available_water_mm', soil_props.get('total_available_water', 75.0))
            # assume linear depletion: after 14 days reach irrigation threshold
            depletion_fraction = min(1.0, days_since_irrigation / max(1.0, 14.0))
            estimated_deficit = soil_limits.get('irrigation_threshold_mm', taw * 0.4) * depletion_fraction
            total_deficit = float(min(taw, estimated_deficit))


        # 4. Generate a 7-day forecast (dynamic). Prefer ML forecaster if available.
        forecast_days = 7
        et_calculator = ETCalculator()
        results = []

        forecast_df = None
        try:
            if forecaster.models_trained and data_pipeline.historical_data is not None:
                # Use the trained forecaster (it returns irrigation predictions too)
                ml_forecast = forecaster.forecast(data_pipeline.historical_data, forecast_days=forecast_days)
                if ml_forecast is not None and not ml_forecast.empty:
                    forecast_df = ml_forecast
        except Exception as e:
            print('Forecaster unavailable or failed, falling back to heuristic:', e)

        if forecast_df is None:
            # Fallback: use last week of NASA data and shift to future days
            try:
                recent = weather_df.tail(7).reset_index(drop=True)
                # Create future 7 days by copying recent and shifting dates forward
                last_date = datetime.strptime(recent.iloc[-1]['date'], '%Y-%m-%d')
                rows = []
                for i in range(forecast_days):
                    src = recent.iloc[i % len(recent)].to_dict()
                    future_date = (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
                    src['date'] = future_date
                    rows.append(src)
                forecast_df = pd.DataFrame(rows)
            except Exception as e:
                return jsonify({'success': False, 'error': f'Could not construct fallback forecast: {e}'}), 500

        # Iterate over forecast days and compute irrigation decision using water balance
        taw = soil_limits.get('total_available_water_mm', soil_props.get('total_available_water', 75.0))
        irrigation_threshold = soil_limits.get('irrigation_threshold_mm', taw * 0.4)
        current_deficit_val = float(total_deficit)

        for _, row in forecast_df.iterrows():
            date = row.get('date')
            temp = float(row.get('temperature', 25.0))
            precip = float(row.get('precipitation', 0.0))
            et0 = float(row.get('et0', 0.0))

            # If et0 not provided, compute it
            if et0 == 0:
                try:
                    day_of_year = datetime.strptime(date, '%Y-%m-%d').timetuple().tm_yday
                    et0 = et_calculator.calculate_et0(temp, float(row.get('relative_humidity', 60.0)),
                                                     float(row.get('wind_speed', 2.0)), float(row.get('solar_radiation', 18.0)),
                                                     latitude, day_of_year)
                except Exception:
                    et0 = 4.0

            # Crop water demand using crop coefficient
            crop_kc = crop_info.get('crop_coefficient', et_calc.get_crop_coefficient(crop_type, days_since_planting))
            crop_water_demand = et0 * crop_kc

            # Update soil moisture deficit
            net_water = precip - crop_water_demand
            current_deficit_val = max(0.0, min(current_deficit_val - net_water, taw))
            soil_moisture_percent = int(100 * (1 - current_deficit_val / taw))
            irrigation_needed = current_deficit_val > irrigation_threshold

            # Prefer ML predicted irrigation amount if available
            predicted_irrigation = None
            if 'irrigation_amount_mm' in forecast_df.columns and not pd.isna(row.get('irrigation_amount_mm')):
                try:
                    predicted_irrigation = float(row.get('irrigation_amount_mm', 0.0))
                except Exception:
                    predicted_irrigation = None

            if predicted_irrigation is None:
                predicted_irrigation = float(max(0.0, current_deficit_val * 0.6)) if irrigation_needed else 0.0

            results.append({
                'date': date,
                'temperature': round(temp, 2),
                'precipitation': round(precip, 2),
                'et0': round(et0, 2),
                'crop_kc': round(crop_kc, 2),
                'crop_water_demand': round(crop_water_demand, 2),
                'soil_moisture_deficit': round(current_deficit_val, 2),
                'soil_moisture_percent': soil_moisture_percent,
                'irrigation_needed': bool(irrigation_needed),
                'predicted_irrigation_mm': round(predicted_irrigation, 2)
            })
        # Start a background retrain for this location (non-blocking)
        try:
            threading.Thread(target=lambda: initialize_ml_models(latitude, longitude), daemon=True).start()
        except Exception as e:
            print('Failed to start background retrain thread:', e)

        # Build soil_properties output with mm-suffixed keys for frontend compatibility
        try:
            root_depth_m = soil_props.get('root_depth', root_depth)
            soil_properties_out = {
                'field_capacity_mm': round(soil_props.get('field_capacity', 0.28) * root_depth_m * 1000, 2),
                'wilting_point_mm': round(soil_props.get('wilting_point', 0.12) * root_depth_m * 1000, 2),
                'total_available_water_mm': round(soil_props.get('total_available_water', soil_limits.get('total_available_water_mm', 75.0)), 2),
                'readily_available_water_mm': round(soil_props.get('readily_available_water', soil_limits.get('readily_available_water_mm', 50.0)), 2),
                'irrigation_threshold_mm': round(soil_limits.get('irrigation_threshold_mm', soil_props.get('total_available_water', 75.0) * 0.4), 2)
            }
        except Exception:
            soil_properties_out = {
                'field_capacity_mm': None,
                'wilting_point_mm': None,
                'total_available_water_mm': None,
                'readily_available_water_mm': None,
                'irrigation_threshold_mm': None
            }

        return jsonify({
            'success': True,
            'location': f"{latitude}, {longitude}",
            'soil_properties': soil_properties_out,
            'soil_limits': soil_limits,
            'soil_properties_raw': soil_props,
            'crop_info': crop_info,
            'initial_deficit_mm': total_deficit,
            'forecast_days': len(results),
            'data': results
        })
    except Exception as e:
        import traceback
        print("Exception in /get_irrigation_data POST:", traceback.format_exc())
        return ( jsonify ({
                'success': False,
                'error': f'Irrigation data generation failed: {str(e)}'} 
            ),
            500
            )
@app.route('/get_model_metrics')
def get_model_metrics():
    """Get model performance metrics"""
    if hasattr(forecaster, 'performance_metrics'):
        return jsonify({
            'success': True,
            'metrics': forecaster.performance_metrics
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Performance metrics not available'
        })


@app.route('/model_status')
def model_status():
    """Return whether models are trained and basic metrics"""
    try:
        trained = bool(getattr(forecaster, 'models_trained', False))
        metrics = getattr(forecaster, 'performance_metrics', {})
        return jsonify({
            'success': True,
            'models_trained': trained,
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/retrain_models', methods=['POST'])
def retrain_models():
    """Retrain models with new data"""
    try:
        data = request.json
        lat = float(data.get('latitude', 9.0))
        lon = float(data.get('longitude', 39.7))
        
        success = initialize_ml_models(lat, lon)
        
        return jsonify({
            'success': success,
            'message': 'Models retrained successfully' if success else 'Model retraining failed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Retraining failed: {str(e)}'
        })

@app.route('/download_forecast')
def download_forecast():
    """Download forecast as CSV"""
    global current_forecast
    
    if current_forecast is not None:
        filename = f"irrigation_forecast_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        current_forecast.to_csv(f'nasa_power_irrigation_app/static/downloads/{filename}', index=False)
        
        return jsonify({
            'success': True,
            'download_url': f'/static/downloads/{filename}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No forecast available to download'
        })

# Initialize models when app starts
try:
    before_first_request = app.before_first_request
except AttributeError:
    # Fallback for older Flask versions
    before_first_request = lambda f: f

def initialize():
    """Initialize ML models before first request"""
    print("🌱 Initializing NASA Power Irrigation App...")

    # Create necessary directories
    os.makedirs('nasa_power_irrigation_app/static/performance', exist_ok=True)
    os.makedirs('nasa_power_irrigation_app/static/downloads', exist_ok=True)

    # Initialize ML models
    initialize_ml_models()
    try:
        generate_performance_graphs()
        print("✅ Performance graphs generated")
    except Exception as e:
        print(f"⚠️ Could not generate performance graphs: {e}")

# Call initialize() manually at startup since @app.before_first_request is not available
initialize()


CORS(app)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
