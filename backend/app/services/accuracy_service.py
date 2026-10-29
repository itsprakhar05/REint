import pandas as pd


def calculate_accuracy(
    forecasts: pd.DataFrame,
    actuals: pd.DataFrame,
) -> dict:
    """
    Compare forecasts with actual generation.

    Both dataframes must contain:
    - startTime
    - generation
    """

    forecasts = forecasts.copy()
    actuals = actuals.copy()

    if "startTime" not in forecasts.columns:
        raise ValueError("Forecast data missing startTime")
    if "startTime" not in actuals.columns:
        raise ValueError("Actual data missing startTime")

    forecasts["startTime"] = pd.to_datetime(forecasts["startTime"], utc=True)
    actuals["startTime"] = pd.to_datetime(actuals["startTime"], utc=True)

    forecasts = (
        forecasts[["startTime", "generation"]]
        .rename(columns={"generation": "forecast_mw"})
        .groupby("startTime", as_index=False)["forecast_mw"]
        .mean()
    )

    actuals = (
        actuals[["startTime", "generation"]]
        .rename(columns={"generation": "actual_mw"})
        .groupby("startTime", as_index=False)["actual_mw"]
        .mean()
    )

    comparison = forecasts.merge(
        actuals[["startTime", "actual_mw"]],
        on="startTime",
        how="inner",
        validate="one_to_one",
    )

    if comparison.empty:
        return {
            "matched_intervals": 0,
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
        }

    comparison["error_mw"] = (
        comparison["forecast_mw"]
        - comparison["actual_mw"]
    )

    mae = comparison["error_mw"].abs().mean()

    rmse = (
        comparison["error_mw"].pow(2).mean()
        ** 0.5
    )

    bias = comparison["error_mw"].mean()

    return {
        "matched_intervals": len(comparison),
        "mae_mw": round(float(mae), 2),
        "rmse_mw": round(float(rmse), 2),
        "bias_mw": round(float(bias), 2),
    }