def route_question(question: str) -> str:
    text = question.lower()

    forecast_keywords = [
        "forecast",
        "predict",
        "prediction",
        "future",
        "next week",
        "next month",
        "time series",
    ]

    analytics_keywords = [
        "profile",
        "missing values",
        "null values",
        "duplicates",
        "correlation",
        "statistics",
        "describe dataset",
        "dataset summary",
    ]

    if any(keyword in text for keyword in forecast_keywords):
        return "forecast"

    if any(keyword in text for keyword in analytics_keywords):
        return "analytics"

    return "sql"