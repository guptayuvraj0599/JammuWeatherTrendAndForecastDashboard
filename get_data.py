from datetime import datetime
from meteostat import Point, Daily
import pandas as pd

# Define Jammu's coordinates
JAMMU_LAT = 32.73
JAMMU_LON = 74.86

# Set time period for historical data (e.g., last 5 years)
start = datetime(2020, 1, 1)
end = datetime.now()

# Get daily historical data
print("Fetching historical data from Meteostat...")
try:
    jammu = Point(JAMMU_LAT, JAMMU_LON, 327)
    data = Daily(jammu, start, end)
    df = data.fetch()
    if not df.empty:
        df.to_csv('jammu_historical_weather.csv')
        print("Successfully saved data to jammu_historical_weather.csv")
    else:
        print("Meteostat returned no data. CSV file not created.")
except Exception as e:
    print(f"An error occurred: {e}")