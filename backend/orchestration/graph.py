import re
import pandas as pd

from backend.orchestration.router import route_question
from backend.agents.sql_agent import SQLAgent
from backend.agents.analytics_agent import AnalyticsAgent
from backend.agents.forecast_agent import ForecastAgent


class MLUEOrchestrator:
    def __init__(self):
        print("Initializing MLUE Orchestrator...")

        self.sql_agent = SQLAgent()
        self.analytics_agent = AnalyticsAgent()
        self.forecast_agent = ForecastAgent()

        print("MLUE Orchestrator ready!")

    def detect_forecast_columns(self, question, df):
        """
        Detect date and target columns from the dataset
        and the user's question.
        """

        # Detect date column
        date_column = None

        for column in df.columns:
            parsed_dates = pd.to_datetime(df[column], errors="coerce")
            valid_ratio = parsed_dates.notna().mean()

            if valid_ratio >= 0.7:
                date_column = column
                break

        if date_column is None:
            return None, None

        # Detect numeric columns
        numeric_columns = df.select_dtypes(include="number").columns.tolist()

        if not numeric_columns:
            return date_column, None

        # Prefer a numeric column explicitly mentioned by the user
        question_lower = question.lower()

        target_column = None

        for column in numeric_columns:
            if column.lower() in question_lower:
                target_column = column
                break

        # If no column was named, use the first numeric column
        if target_column is None:
            target_column = numeric_columns[0]

        return date_column, target_column

    def detect_forecast_periods(self, question):
        """
        Extract forecast horizon, such as:
        'next 5 days' -> 5
        'next 3 weeks' -> 21
        """

        question_lower = question.lower()

        match = re.search(
            r"next\s+(\d+)\s+(day|days|week|weeks|month|months)",
            question_lower,
        )

        if not match:
            return 7

        number = int(match.group(1))
        unit = match.group(2)

        if "week" in unit:
            return number * 7

        if "month" in unit:
            return number * 30

        return number

    def run(self, question):
        route = route_question(question)

        print(f"\nQuestion: {question}")
        print(f"Selected agent: {route}")

        if route == "sql":
            result = self.sql_agent.run(question)

        elif route == "analytics":
            result = self.analytics_agent.run("profile")

        elif route == "forecast":
            df = self.forecast_agent.load_data()

            date_column, target_column = self.detect_forecast_columns(
                question,
                df,
            )

            if date_column is None:
                result = {
                    "success": False,
                    "message": "I couldn't detect a date column in this dataset.",
                }

            elif target_column is None:
                result = {
                    "success": False,
                    "message": "I couldn't detect a numeric column to forecast.",
                }

            else:
                periods = self.detect_forecast_periods(question)

                result = self.forecast_agent.forecast(
                    date_column=date_column,
                    target_column=target_column,
                    periods=periods,
                    method="linear_trend",
                )

        else:
            result = {
                "success": False,
                "message": "Could not determine the correct agent.",
            }

        return {
            "question": question,
            "route": route,
            "result": result,
        }

    def close(self):
        self.sql_agent.close()
        self.analytics_agent.close()
        self.forecast_agent.close()