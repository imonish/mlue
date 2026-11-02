
import pandas as pd
import numpy as np

from backend.database.database import DatabaseManager


class AnalyticsAgent:

    def __init__(self, database_path="data/analytics.duckdb"):
        self.db = DatabaseManager(database_path)

        print("MLUE Analytics Agent initialized!")

    def load_data(self, table_name="dataset"):
        """Load the DuckDB table into Pandas."""

        # Table name is fixed to the validated dataset table
        return self.db.execute_query(
            f"SELECT * FROM {table_name}"
        )

    def profile_dataset(self):
        """Generate a complete dataset profile."""

        df = self.load_data()

        numeric_columns = df.select_dtypes(
            include=np.number
        ).columns.tolist()

        categorical_columns = df.select_dtypes(
            include=["object", "category", "string"]
        ).columns.tolist()

        profile = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "missing_values": (
                df.isnull().sum().to_dict()
            ),
            "duplicate_rows": int(
                df.duplicated().sum()
            ),
        }

        if numeric_columns:
            profile["statistics"] = (
                df[numeric_columns]
                .describe()
                .round(2)
                .to_dict()
            )

        return profile

    def revenue_analysis(self):
        """Analyze product revenue when required columns exist."""

        df = self.load_data()

        required = {"product", "quantity", "price"}

        if not required.issubset(df.columns):
            return {
                "success": False,
                "message": (
                    "Dataset does not contain "
                    "product, quantity and price columns."
                ),
            }

        df["revenue"] = (
            df["quantity"] * df["price"]
        )

        product_revenue = (
            df.groupby("product", as_index=False)
            ["revenue"]
            .sum()
            .sort_values(
                "revenue",
                ascending=False
            )
        )

        total_revenue = float(
            df["revenue"].sum()
        )

        top_product = (
            product_revenue.iloc[0].to_dict()
        )

        return {
            "success": True,
            "total_revenue": total_revenue,
            "top_product": top_product,
            "product_revenue": (
                product_revenue.to_dict(
                    orient="records"
                )
            ),
        }

    def correlation_analysis(self):
        """Calculate correlations between numeric columns."""

        df = self.load_data()

        numeric_df = df.select_dtypes(
            include=np.number
        )

        if numeric_df.shape[1] < 2:
            return {
                "success": False,
                "message": (
                    "At least two numeric columns "
                    "are required."
                ),
            }

        correlation = (
            numeric_df.corr()
            .round(3)
        )

        return {
            "success": True,
            "columns": correlation.columns.tolist(),
            "matrix": correlation.to_dict(),
        }

    def run(self, analysis_type="profile"):
        """Execute a selected analytics task."""

        if analysis_type == "profile":
            return self.profile_dataset()

        elif analysis_type == "revenue":
            return self.revenue_analysis()

        elif analysis_type == "correlation":
            return self.correlation_analysis()

        else:
            raise ValueError(
                f"Unknown analysis type: {analysis_type}"
            )

    def close(self):
        self.db.close()
