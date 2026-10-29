import pandas as pd

from app.services.accuracy_service import calculate_accuracy
from app.services.forcast_selection import select_latest_eligible_forecasts


def test_calculate_accuracy():
    forecasts = pd.DataFrame({
        "startTime": ["10:00", "10:30", "11:00"],
        "generation": [100, 120, 140],
    })

    actuals = pd.DataFrame({
        "startTime": ["10:00", "10:30", "11:00"],
        "generation": [90, 130, 140],
    })

    result = calculate_accuracy(forecasts, actuals)

    assert result["matched_intervals"] == 3
    assert result["mae_mw"] == 6.67
    assert result["rmse_mw"] == 8.16
    assert result["bias_mw"] == 0.0


def test_select_latest_eligible_forecasts_keeps_latest_record_per_period():
    forecasts = pd.DataFrame({
        "startTime": [
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:30:00Z",
        ],
        "publishTime": [
            "2026-01-01T00:05:00Z",
            "2026-01-01T00:15:00Z",
            "2026-01-01T00:20:00Z",
        ],
        "generation": [100, 120, 110],
    })

    selected = select_latest_eligible_forecasts(forecasts, "2026-01-01T00:20:00Z")

    assert len(selected) == 2
    assert selected["generation"].tolist() == [120, 110]


def test_calculate_accuracy_handles_duplicate_timestamps():
    forecasts = pd.DataFrame({
        "startTime": ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "2026-01-01T00:30:00Z"],
        "generation": [100, 120, 110],
    })

    actuals = pd.DataFrame({
        "startTime": ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "2026-01-01T00:30:00Z"],
        "generation": [90, 110, 100],
    })

    result = calculate_accuracy(forecasts, actuals)

    assert result["matched_intervals"] == 2
    assert result["mae_mw"] == 10.0
    assert result["rmse_mw"] == 10.0