from pprint import pprint

from backend.database.database import DatabaseManager
from backend.database.dataset_loader import load_csv
from backend.agents.forecast_agent import ForecastAgent


def main():
    # Load the time-series dataset into DuckDB
    db = DatabaseManager()
    try:
        result = load_csv(
            "data/datasets/daily_sales.csv",
            db.connection,
            table_name="dataset",
        )
        print("Dataset loaded:")
        pprint(result)
    finally:
        db.close()

    # Test the Forecast Agent
    agent = ForecastAgent()

    try:
        print("\n1. MOVING AVERAGE FORECAST")
        pprint(
            agent.forecast(
                date_column="date",
                target_column="sales",
                periods=5,
                method="moving_average",
                window=3,
            )
        )

        print("\n2. LINEAR TREND FORECAST")
        pprint(
            agent.forecast(
                date_column="date",
                target_column="sales",
                periods=5,
                method="linear_trend",
            )
        )
    finally:
        agent.close()


if __name__ == "__main__":
    main()