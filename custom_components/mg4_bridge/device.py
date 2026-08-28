from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


class Mg4CarSyncedMixin:
    """Poll hedefi yalnızca arabadan en az bir push geldikten sonra kullanılabilir."""

    _car_sync_key: str

    def _car_store(self) -> dict:
        return self.hass.data[DOMAIN][self._entry.entry_id]["data"]

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        data = self._car_store()
        if data.get("online") is False:
            return False
        return self._car_sync_key in data


def bridge_device(prefix: str, name: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, prefix)},
        name=name,
        manufacturer="MG",
        model="MG4 EH32",
    )
