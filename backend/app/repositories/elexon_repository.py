import httpx

FUELHH_URL = (
    "https://data.elexon.co.uk/bmrs/api/v1/"
    "datasets/FUELHH/stream"
)

WINDFOR_URL = (
    "https://data.elexon.co.uk/bmrs/api/v1/"
    "datasets/WINDFOR/stream"
)


def filter_wind_actuals(rows: list[dict]) -> list[dict]:
    if not rows:
        return []

    filtered = []
    for row in rows:
        fuel_type = str(row.get("fuelType", "")).upper()
        if fuel_type == "WIND":
            filtered.append(row)
    return filtered


async def fetch_dataset(
    url: str,
    params: dict,
) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected Elexon response format")

    return data