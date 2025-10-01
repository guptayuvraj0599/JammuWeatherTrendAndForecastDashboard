# Jammu Weather Trend & Forecast Dashboard

## Project Synopsis
This is a web-based dashboard designed to provide real-time weather information and historical climate trend analysis for the Jammu region. The project aims to address the challenges posed by frequent extreme weather events like cloudbursts and landslides by providing an integrated, citizen-friendly platform for weather insights.

The dashboard includes:
- **Historical Analysis**: Visualizations of long-term rainfall and temperature trends.
- **Weather Forecasting**: A 7-day and 15-day rainfall forecast using time-series models.
- **Real-time Updates**: Current weather conditions fetched from a live API.
- **Risk Mapping**: An interactive map highlighting disaster-prone areas.

## Technical Stack
- **Framework**: Streamlit for building the interactive dashboard.
- **Data Collection**:
    - **Historical Data**: Meteostat API for past weather data.
    - **Real-time Data**: OpenWeather API for current weather conditions.
- **Forecasting Model**: Prophet, a time-series forecasting model developed by Meta.
- **Visualization**: Plotly for charts and Folium for interactive maps.
- **Deployment**: Streamlit Community Cloud.

## How to Run the Project Locally
To run this project on your local machine, follow these steps:

## Clone the repository
git clone 