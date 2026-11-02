import pandas as pd
import numpy as np
from backend.database.database import DatabaseManager


class ForecastAgent:
    def __init__(self, database_path="data/analytics.duckdb"):
        self.db = DatabaseManager(database_path)
        print("MLUE Forecast Agent initialized!")

    def load_data(self, table_name="dataset"):
        return self.db.execute_query(f"SELECT * FROM {table_name}")

    def forecast(
        self,
        date_column,
        target_column,
        periods=7,
        frequency="D",
        method="moving_average",
        window=3,
    ):
        df = self.load_data()

        # Validate requested columns
        if date_column not in df.columns:
            return {
                "success": False,
                "message": f"Date column '{date_column}' was not found.",
            }

        if target_column not in df.columns:
            return {
                "success": False,
                "message": f"Target column '{target_column}' was not found.",
            }

        # Prepare time-series data
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df[target_column] = pd.to_numeric(df[target_column], errors="coerce")

        df = df[[date_column, target_column]].dropna()
        df = df.groupby(date_column, as_index=False)[target_column].sum()
        df = df.sort_values(date_column)

        if len(df) < 2:
            return {
                "success": False,
                "message": "At least two valid time-series records are required.",
            }

        if periods < 1:
            return {
                "success": False,
                "message": "Forecast periods must be at least 1.",
            }

        # Create future dates
        last_date = df[date_column].max()
        future_dates = pd.date_range(
            start=last_date,
            periods=periods + 1,
            freq=frequency,
        )[1:]

        values = df[target_column].astype(float)

        # Forecast using a simple baseline
        if method == "moving_average":
            forecast_value = values.tail(window).mean()
            predictions = [float(forecast_value)] * periods

        elif method == "linear_trend":
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1)

            future_x = np.arange(len(values), len(values) + periods)
            predictions = (slope * future_x + intercept).tolist()

        else:
            return {
                "success": False,
                "message": f"Unknown forecast method: {method}",
            }

        forecast_df = pd.DataFrame({
            "date": future_dates,
            "forecast": predictions,
        })

        return {
            "success": True,
            "method": method,
            "target_column": target_column,
            "forecast": forecast_df.to_dict(orient="records"),
        }

    def close(self):
        self.db.close()