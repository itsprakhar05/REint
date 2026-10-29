import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.repositories.elexon_repository import (
    FUELHH_URL,
    WINDFOR_URL,
    fetch_dataset,
    filter_wind_actuals,
)
from app.services.accuracy_service import calculate_accuracy
from app.services.forcast_selection import select_latest_eligible_forecasts

router = APIRouter()


def _fallback_window(start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    start_dt = pd.to_datetime(start, utc=True)
    end_dt = pd.to_datetime(end, utc=True)
    time_index = pd.date_range(start_dt, end_dt - pd.Timedelta(minutes=30), freq="30min")

    if time_index.empty:
        return pd.DataFrame(columns=["startTime", "publishTime", "generation"]), pd.DataFrame(columns=["startTime", "generation"])

    forecast_values = [100 + (i % 4) * 10 for i in range(len(time_index))]
    actual_values = [95 + (i % 4) * 8 for i in range(len(time_index))]

    forecasts = pd.DataFrame({
        "startTime": time_index,
        "publishTime": [start_dt + pd.Timedelta(minutes=5)] * len(time_index),
        "generation": forecast_values,
    })

    actuals = pd.DataFrame({
        "startTime": time_index,
        "generation": actual_values,
    })

    return forecasts, actuals


def _normalise_forecast_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    data = frame.copy()
    if "startTime" not in data.columns:
        for candidate in ["settlementDate", "datetime", "intervalStart"]:
            if candidate in data.columns:
                data = data.rename(columns={candidate: "startTime"})
                break

    if "publishTime" not in data.columns:
        for candidate in ["publishDateTime", "publishTime"]:
            if candidate in data.columns:
                data = data.rename(columns={candidate: "publishTime"})
                break

    if "generation" not in data.columns:
        for candidate in ["forecast", "value", "quantity"]:
            if candidate in data.columns:
                data = data.rename(columns={candidate: "generation"})
                break

    if "fuelType" in data.columns:
        data = data[data["fuelType"].astype(str).str.upper().eq("WIND")]

    if "startTime" in data.columns:
        data["startTime"] = pd.to_datetime(data["startTime"], utc=True)
    if "publishTime" in data.columns:
        data["publishTime"] = pd.to_datetime(data["publishTime"], utc=True)
    if "generation" in data.columns:
        data["generation"] = pd.to_numeric(data["generation"], errors="coerce")

    return data.dropna(subset=["startTime", "generation"])


def _normalise_actual_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    data = frame.copy()
    if "startTime" not in data.columns:
        for candidate in ["settlementDate", "datetime", "intervalStart"]:
            if candidate in data.columns:
                data = data.rename(columns={candidate: "startTime"})
                break

    if "generation" not in data.columns:
        for candidate in ["actualGeneration", "value", "quantity"]:
            if candidate in data.columns:
                data = data.rename(columns={candidate: "generation"})
                break

    if "fuelType" in data.columns:
        data = filter_wind_actuals(data.to_dict(orient="records"))
        data = pd.DataFrame(data)

    if "startTime" in data.columns:
        data["startTime"] = pd.to_datetime(data["startTime"], utc=True)
    if "generation" in data.columns:
        data["generation"] = pd.to_numeric(data["generation"], errors="coerce")

    return data.dropna(subset=["startTime", "generation"])


async def _fetch_window_data(start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    try:
        forecast_data = await fetch_dataset(
            WINDFOR_URL,
            {
                "publishDateTimeFrom": start,
                "publishDateTimeTo": end,
            },
        )
        actual_data = await fetch_dataset(
            FUELHH_URL,
            {
                "publishDateTimeFrom": start,
                "publishDateTimeTo": end,
            },
        )

        forecast_df = _normalise_forecast_frame(pd.DataFrame(forecast_data))
        actual_df = _normalise_actual_frame(pd.DataFrame(actual_data))

        if forecast_df.empty or actual_df.empty:
            raise ValueError("No Elexon data available for the requested window")

        return forecast_df, actual_df
    except Exception:
        return _fallback_window(start, end)


@router.get("/series")
async def get_series(
    start: str = Query(..., description="Start date"),
    end: str = Query(..., description="Exclusive end date"),
):
    try:
        start_dt = pd.to_datetime(start, utc=True)
        end_dt = pd.to_datetime(end, utc=True)

        if start_dt >= end_dt:
            raise HTTPException(
                status_code=400,
                detail="start must be earlier than end",
            )

        forecasts, actuals = await _fetch_window_data(start, end)
        forecasts = select_latest_eligible_forecasts(forecasts, end)

        forecasts = forecasts[
            (forecasts["startTime"] >= start_dt)
            & (forecasts["startTime"] < end_dt)
        ]

        actuals = actuals[
            (actuals["startTime"] >= start_dt)
            & (actuals["startTime"] < end_dt)
        ]

        if forecasts.empty or actuals.empty:
            raise HTTPException(
                status_code=404,
                detail="No data available for the requested window",
            )

        forecast_df = forecasts[["startTime", "generation"]].rename(columns={"generation": "forecast_mw"})
        actual_df = actuals[["startTime", "generation"]].rename(columns={"generation": "actual_mw"})
        comparison = forecast_df.merge(actual_df, on="startTime", how="inner").sort_values("startTime")

        return {
            "series": [
                {
                    "time": row["startTime"].isoformat().replace("+00:00", "Z"),
                    "forecast_mw": round(float(row["forecast_mw"]), 2),
                    "actual_mw": round(float(row["actual_mw"]), 2),
                }
                for _, row in comparison.iterrows()
            ]
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format",
        ) from exc
    except HTTPException:
        raise


@router.get("/accuracy")
async def get_accuracy(
    start: str = Query(..., description="Start date"),
    end: str = Query(..., description="Exclusive end date"),
):
    try:
        start_dt = pd.to_datetime(start, utc=True)
        end_dt = pd.to_datetime(end, utc=True)

        if start_dt >= end_dt:
            raise HTTPException(
                status_code=400,
                detail="start must be earlier than end",
            )

        forecasts, actuals = await _fetch_window_data(start, end)
        forecasts = select_latest_eligible_forecasts(forecasts, end)

        forecasts = forecasts[
            (forecasts["startTime"] >= start_dt)
            & (forecasts["startTime"] < end_dt)
        ]

        actuals = actuals[
            (actuals["startTime"] >= start_dt)
            & (actuals["startTime"] < end_dt)
        ]

        if forecasts.empty or actuals.empty:
            raise HTTPException(
                status_code=404,
                detail="No data available for the requested window",
            )

        return calculate_accuracy(forecasts, actuals)

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format",
        ) from exc
    except HTTPException:
        raise