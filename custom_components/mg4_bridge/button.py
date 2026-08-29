from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, CONF_PREFIX
from .device import bridge_device


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    prefix = entry.data[CONF_PREFIX]
    btn = Mg4RefreshButton(hass, entry)
    btn.entity_id = f"button.{prefix}_refresh"
    async_add_entities([btn])


class Mg4RefreshButton(ButtonEntity):
    """Arabanın bir sonraki poll'unda full push tetikler."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._prefix = entry.data[CONF_PREFIX]
        self._attr_unique_id = f"{self._prefix}_refresh"
        self._attr_device_info = bridge_device(self._prefix, entry.data[CONF_NAME])

    async def async_press(self) -> None:
        # State = last press timestamp (HA Button); araba bunu poll eder.
        return
