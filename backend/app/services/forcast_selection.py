import pandas as pd


def select_latest_eligible_forecasts(
    forecasts: pd.DataFrame,
    decision_cutoff: str,
) -> pd.DataFrame:
    if forecasts.empty:
        return forecasts.copy()

    data = forecasts.copy()

    required_fields = {"startTime", "publishTime"}
    missing = required_fields - set(data.columns)
    if missing:
        raise ValueError(
            "Forecast data missing required columns: "
            f"{sorted(missing)}"
        )

    data["startTime"] = pd.to_datetime(data["startTime"], utc=True)
    data["publishTime"] = pd.to_datetime(data["publishTime"], utc=True)

    cutoff = pd.to_datetime(decision_cutoff, utc=True)
    eligible = data[data["publishTime"] <= cutoff]

    if eligible.empty:
        return eligible.sort_values("startTime").reset_index(drop=True)

    selected = (
        eligible.sort_values(["startTime", "publishTime"])
        .drop_duplicates(subset=["startTime"], keep="last")
        .sort_values("startTime")
        .reset_index(drop=True)
    )

    return selected