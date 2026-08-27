from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# ~11 m; aynı noktada Nominatim’i tekrarlamamak için
_COORD_ROUND = 4


def geocode_cache_key(lat: float, lon: float) -> str:
    return f"{round(float(lat), _COORD_ROUND)},{round(float(lon), _COORD_ROUND)}"


async def async_reverse_geocode(hass: HomeAssistant, lat: float, lon: float) -> str | None:
    """OpenStreetMap Nominatim ile enlem/boylam → adres metni."""
    session = async_get_clientsession(hass)
    url = "https://nominatim.openstreetmap.org/reverse"
    params: dict[str, Any] = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 0,
    }
    headers = {"User-Agent": "HomeAssistant-mg4_bridge/2.0 (HA custom component)"}
    try:
        async with session.get(
            url,
            params=params,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                _LOGGER.debug("Nominatim HTTP %s", resp.status)
                return None
            data = await resp.json(content_type=None)
            name = data.get("display_name") if isinstance(data, dict) else None
            return str(name) if name else None
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Reverse geocode failed: %s", err)
        return None
