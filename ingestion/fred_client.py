from dataclasses import dataclass

import requests

from config.settings import FRED_API_KEY, FRED_BASE_URL, ENV_PATH


@dataclass(frozen=True)
class FredObservation:
    series_id: str
    record_date: str
    value: float


class FredClient:
    def __init__(self, api_key=None, base_url=None, timeout=30):
        self.api_key = api_key if api_key is not None else FRED_API_KEY
        self.base_url = (base_url or FRED_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        if not self.api_key:
            raise RuntimeError(
                f"FRED_API_KEY is not set. Add it to your private {ENV_PATH} file."
            )

    def get_latest_observation(self, series_id, lookback_limit=10):
        response = self.session.get(
            f"{self.base_url}/series/observations",
            params={
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": lookback_limit,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        if "error_code" in data:
            raise RuntimeError(
                f"FRED API error {data['error_code']}: {data.get('error_message')}"
            )

        for observation in data.get("observations", []):
            raw_value = observation.get("value")
            if raw_value in (None, "", "."):
                continue

            try:
                value = float(raw_value)
            except ValueError:
                continue

            return FredObservation(
                series_id=series_id,
                record_date=observation["date"],
                value=value,
            )

        raise RuntimeError(f"No numeric observations found for FRED series {series_id}.")
