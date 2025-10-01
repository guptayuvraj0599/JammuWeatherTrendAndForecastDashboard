import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime
from meteostat import Point, Daily
from prophet import Prophet
import os

# --- Configuration & Secrets ---
# Use Streamlit secrets for your API key
# Create a .streamlit/secrets.toml file with:
# [api]
# openweather_api_key = "YOUR_OPENWEATHER_API_KEY"
try:
    OPENWEATHER_API_KEY = st.secrets["api"]["openweather_api_key"]
except (KeyError, FileNotFoundError):
    st.error("OpenWeather API key not found. Please add it to your .streamlit/secrets.toml file.")
    OPENWEATHER_API_KEY = None

# Define Jammu's coordinates
JAMMU_LAT = 32.73
JAMMU_LON = 74.86

# --- Data Fetching Functions ---

@st.cache_data
def get_historical_data(lat, lon, start_date, end_date):
    """
    Fetches historical weather data from Meteostat.
    Uses a local CSV as a fallback if the API data is insufficient.
    """
    st.info("Fetching historical data from Meteostat...")
    
    # Try fetching from Meteostat API
    try:
        location = Point(lat, lon, 327)
        data = Daily(location, start_date, end_date)
        df = data.fetch()
        
        # Check if the fetched data is sufficient
        if not df.empty and 'prcp' in df.columns and len(df.dropna()) > 30: # Prophet needs a good amount of data
            st.success("Successfully fetched historical data from Meteostat.")
            return df
        else:
            st.warning("Meteostat API returned insufficient data. Using a fallback dataset.")
    except Exception as e:
        st.error(f"Error fetching data from Meteostat: {e}. Using a fallback dataset.")
        
    # Fallback to local CSV file
    try:
        df_fallback = pd.read_csv('jammu_historical_weather.csv', index_col=0, parse_dates=True)
        st.success("Successfully loaded data from local fallback CSV.")
        return df_fallback
    except FileNotFoundError:
        st.error("Fallback file 'jammu_historical_weather.csv' not found. Please ensure it exists.")
        return pd.DataFrame()

def get_real_time_data(api_key, lat, lon):
    """
    Fetches real-time weather data from OpenWeather API.
    """
    if not api_key:
        return None
    
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching real-time weather data: {e}")
        return None

# --- Modeling Function ---
def get_forecast_data(historical_df):
    """
    Runs Prophet to generate a 15-day rainfall forecast.
    """
    if historical_df.empty or 'prcp' not in historical_df.columns:
        return pd.DataFrame()
    
    df_prophet = historical_df.reset_index().rename(columns={'time': 'ds', 'prcp': 'y'})
    df_prophet = df_prophet[['ds', 'y']] # Select only the required columns
    
    # Drop rows with missing values
    df_prophet.dropna(inplace=True)
    
    # Check if there is enough data for Prophet
    if len(df_prophet) < 30: # Prophet needs a minimum number of data points
        st.warning(f"Not enough data to generate a forecast. Only {len(df_prophet)} data points available.")
        return pd.DataFrame()

    m = Prophet(daily_seasonality=True, weekly_seasonality=False, yearly_seasonality=True)
    m.fit(df_prophet)
    future = m.make_future_dataframe(periods=15)
    forecast = m.predict(future)
    return forecast

# --- Dashboard Layout and Content ---

st.title("Jammu Weather Trend & Forecast Dashboard")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Historical Trends", "Forecast", "Real-time Weather", "Risk Map"])

# Fetch data for all tabs once at the top
historical_df = get_historical_data(JAMMU_LAT, JAMMU_LON, datetime(2020, 1, 1), datetime.now())
forecast_df = get_forecast_data(historical_df)
real_time_data = get_real_time_data(OPENWEATHER_API_KEY, JAMMU_LAT, JAMMU_LON)

# --- Historical Trends Tab ---
with tab1:
    st.header("Historical Weather Trends")
    if not historical_df.empty and 'prcp' in historical_df.columns and 'tavg' in historical_df.columns:
        # Rainfall chart
        fig_rainfall = px.line(historical_df, x=historical_df.index, y='prcp', title='Daily Rainfall in Jammu (mm)')
        st.plotly_chart(fig_rainfall)
        
        # Temperature chart
        fig_temp = px.line(historical_df, x=historical_df.index, y='tavg', title='Average Daily Temperature in Jammu (°C)')
        st.plotly_chart(fig_temp)
    else:
        st.warning("Historical data could not be loaded or is incomplete.")

# --- Forecast Tab ---
with tab2:
    st.header("Rainfall Forecast")
    if not forecast_df.empty:
        fig_forecast = px.line(forecast_df, x='ds', y='yhat', title='15-Day Rainfall Forecast')
        fig_forecast.add_scatter(x=forecast_df['ds'], y=forecast_df['yhat_lower'], fill='tonexty', mode='lines', line_color='rgba(0,0,0,0)', name='Lower Bound')
        fig_forecast.add_scatter(x=forecast_df['ds'], y=forecast_df['yhat_upper'], fill='tonexty', mode='lines', line_color='rgba(0,0,0,0)', name='Upper Bound')
        st.plotly_chart(fig_forecast)
        
        # Display forecast data in a table for clarity
        st.subheader("Forecast Data")
        st.dataframe(forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(15).set_index('ds'))
    else:
        st.warning("Forecast could not be generated. Check the historical data.")

# --- Real-time Weather Tab ---
with tab3:
    st.header("Real-time Weather")
    if real_time_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Temperature", value=f"{real_time_data['main']['temp']} °C")
        with col2:
            st.metric(label="Humidity", value=f"{real_time_data['main']['humidity']}%")
        with col3:
            st.metric(label="Wind Speed", value=f"{real_time_data['wind']['speed']} m/s")
        
        st.write(f"**Current Condition:** {real_time_data['weather'][0]['description'].capitalize()}")
        st.write(f"**Last Updated:** {datetime.fromtimestamp(real_time_data['dt']).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("Real-time weather data could not be loaded. Please check your API key.")

# --- Risk Map Tab ---
with tab4:
    st.header("Disaster-Prone Areas & Risk Map")
    
    # Dummy data for landslide/cloudburst hotspots.
    # In a real project, this would come from your 'Disaster reports' dataset.
    landslide_hotspots = [
        {"lat": 32.78, "lon": 74.92, "name": "Nagrota", "risk": "High"},
        {"lat": 32.75, "lon": 74.88, "name": "Jammu City", "risk": "Medium"},
    ]
    
    # Create the Folium map centered on Jammu
    m = folium.Map(location=[JAMMU_LAT, JAMMU_LON], zoom_start=11)
    
    # Add markers for hotspots
    for hotspot in landslide_hotspots:
        color = "red" if hotspot['risk'] == "High" else "orange"
        icon = "cloud" if "Cloudburst" in hotspot['name'] else "bolt"
        
        folium.Marker(
            location=[hotspot['lat'], hotspot['lon']],
            popup=f"**{hotspot['name']}**<br>Risk: {hotspot['risk']}",
            icon=folium.Icon(color=color, icon=icon, prefix='fa')
        ).add_to(m)

    st_folium(m)