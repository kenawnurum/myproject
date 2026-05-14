    Data layer: NASA POWER, live weather, soil inputs, storage
    Domain layer: ET calculation and irrigation prediction
    Delivery layer: Flask web app and Expo mobile app
    Presentation layer: HTML templates, CSS, and React Native UI

Data Acquisition and Preprocessing: We successfully fetched daily weather data (including min/max temperature, humidity, solar radiation, wind speed, and rainfall) for a specific location and period using the NASA POWER API. The raw data was then rigorously preprocessed, including handling invalid values and imputing missing data using a smart_fill function. We also calculated the daily mean temperature (tavg_c) and incorporated elevation data.
    
            Python code
               ↓
            Creates URL
               ↓
            Sends HTTP request to NASA server
               ↓
            NASA processes request
               ↓
            NASA returns JSON data
               ↓
            Python reads the JSON

ET0 Calculation: We computed the reference evapotranspiration (ET0_FAO56) using the FAO-56 Penman-Monteith equation, which served as our ground truth for model training.
 Exploratory Data Analysis (EDA) and Visualization: We performed several visualizations to understand the data better:
  Time-series plots for ET0_FAO56, tavg_c, and rain_mm showed temporal patterns.
Autocorrelation (ACF) and Partial Autocorrelation (PACF) plots confirmed the time-series nature of ET0, indicating suitability for sequence modeling.
Feature importance analysis revealed the most influential weather parameters for ET0 prediction.
A pairplot was generated to visualize relationships between weather features and predicted ET0, and a scatter plot showed Tmax vs. RH colored by ET0.

Feature Engineering and Scaling: We identified and selected relevant features for our models. The data was split into training and testing sets, and numerical features were scaled using StandardScaler to optimize model performance.

Model Development and Evaluation: We implemented and evaluated three different machine learning models:
K-Nearest Neighbors (KNN) Regressor: A baseline model was trained and evaluated.
Random Forest Regressor: A robust ensemble model was trained, and its parameters were tuned. Its performance was thoroughly evaluated, and a residual plot confirmed good model fit.
XGBoost Regressor: An advanced gradient boosting model was implemented, demonstrating superior performance with lower RMSE and higher R2 scores.
Long Short-Term Memory (LSTM) Neural Network: A deep learning model, particularly suited for sequential data, was implemented after reshaping the input data. Its performance was also evaluated.

 MLflow Integration: Throughout the model development, we leveraged MLflow to track experiments, log model parameters, and metrics (RMSE, R2) for systematic comparison and reproducibility.

Model Persistence and Deployment: The best-performing Random Forest model and its corresponding StandardScaler were saved using pickle. We demonstrated how these saved artifacts could be loaded and used to make predictions on new, unseen data, providing a foundation for potential real-time deployment.

This notebook provides a comprehensive workflow for ET0 prediction, from data acquisition to model deployment, utilizing various machine learning techniques and best practices for MLOps with MLflow.
# NASA Power Irrigation App

## Project Structure

```text
.
├── app.py
├── config.py
├── dr_store.py
├── et_calculator.py
├── irrigation_predictor.py
├── nasa_power.py
├── requirements.txt
├── soil_properties.py
├── weather_live.py
├── static/
│   └── style.css
├── templates/
│   ├── dr_history.html
│   ├── forecast.html
│   ├── index.html
│   └── performance.html
├── nasa_power_irrigation_app/
│   └── static/
│       ├── downloads/
│       └── performance/
├── screens/
│   └── IrrigationScreen.js
├── smart-irrigation-app/
│   ├── App.js
│   ├── app.json
│   ├── eslint.config.js
│   ├── expo-env.d.ts
│   ├── package.json
│   ├── README.md
│   ├── tsconfig.json
│   ├── app/
│   │   ├── _layout.tsx
│   │   ├── modal.tsx
│   │   └── (tabs)/
│   │       ├── _layout.tsx
│   │       ├── explore.tsx
│   │       └── index.tsx
│   ├── app-example/
│   ├── assets/
│   │   └── images/
│   ├── components/
│   │   ├── external-link.tsx
│   │   ├── haptic-tab.tsx
│   │   ├── hello-wave.tsx
│   │   ├── parallax-scroll-view.tsx
│   │   ├── themed-text.tsx
│   │   ├── themed-view.tsx
│   │   └── ui/
│   │       ├── collapsible.tsx
│   │       ├── icon-symbol.ios.tsx
│   │       └── icon-symbol.tsx
│   ├── constants/
│   │   └── theme.ts
│   ├── hooks/
│   │   ├── use-color-scheme.ts
│   │   ├── use-color-scheme.web.ts
│   │   └── use-theme-color.ts
│   ├── screens/
│   │   └── components/
│   │       ├── ForcastCard.js
│   │       └── IrrigationScreen.js
│   └── scripts/
│       └── reset-project.js
└── venv311/
    ├── Include/
    ├── Lib/
    │   └── site-packages/
    ├── Scripts/
    └── share/

```

## Short Overview

- Backend: Flask app for irrigation prediction, ET0 estimation, soil properties, and weather integration.
- Web UI: HTML templates and static assets served by Flask.
- Mobile UI: Expo / React Native app under `smart-irrigation-app/`.
- Generated outputs: downloads and performance artifacts under `nasa_power_irrigation_app/static/`.
