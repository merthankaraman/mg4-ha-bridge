from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, CONF_PREFIX, DOMAIN, SIGNAL_UPDATE
from .device import Mg4CarSyncedMixin, bridge_device


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    prefix = entry.data[CONF_PREFIX]
    hvac = Mg4HvacSwitch(hass, entry)
    hvac.entity_id = f"switch.{prefix}_hvac"
    charging = Mg4ChargingSwitch(hass, entry)
    charging.entity_id = f"switch.{prefix}_charging"
    async_add_entities([hvac, charging])


class Mg4HvacSwitch(Mg4CarSyncedMixin, SwitchEntity):
    """Araba → HA: push ile senkron; HA → araba: poll ile uygular."""

    _car_sync_key = "hvac"
    _attr_has_entity_name = True
    _attr_translation_key = "hvac"
    _attr_icon = "mdi:air-conditioner"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._prefix = entry.data[CONF_PREFIX]
        self._attr_unique_id = f"{self._prefix}_hvac"
        self._attr_device_info = bridge_device(self._prefix, entry.data[CONF_NAME])
        self._pending_ha_target: bool | None = None
        self._pending_car_value: bool | None = None
        self._last_car_value: bool | None = None

    def _data(self) -> dict:
        return self._car_store()

    def _car_hvac(self) -> bool | None:
        raw = self._data().get("hvac")
        if isinstance(raw, bool):
            return raw
        return self._last_car_value

    async def async_added_to_hass(self) -> None:
        raw = self._data().get("hvac")
        if isinstance(raw, bool):
            self._attr_is_on = raw
            self._last_car_value = raw
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_UPDATE}_{self._entry.entry_id}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        raw = self._data().get("hvac")
        if not isinstance(raw, bool):
            self.async_write_ha_state()
            return

        if self._pending_ha_target is not None:
            if raw == self._pending_ha_target:
                self._pending_ha_target = None
                self._pending_car_value = None
            elif (
                self._pending_car_value is not None
                and raw != self._pending_car_value
            ):
                self._pending_ha_target = None
                self._pending_car_value = None
            else:
                self.async_write_ha_state()
                return

        if self._attr_is_on != raw:
            self._attr_is_on = raw
        self._last_car_value = raw
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self._pending_ha_target = True
        self._pending_car_value = self._car_hvac()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self._pending_ha_target = False
        self._pending_car_value = self._car_hvac()
        self.async_write_ha_state()


class Mg4ChargingSwitch(Mg4CarSyncedMixin, SwitchEntity):
    """Şarj durumu + başlat/durdur (poll → setChargingControlSwitch)."""

    _car_sync_key = "charging"
    _attr_has_entity_name = True
    _attr_translation_key = "charging"
    _attr_icon = "mdi:ev-station"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._prefix = entry.data[CONF_PREFIX]
        self._attr_unique_id = f"{self._prefix}_charging_switch"
        self._attr_device_info = bridge_device(self._prefix, entry.data[CONF_NAME])
        self._pending_ha_target: bool | None = None
        self._pending_car_value: bool | None = None
        self._last_car_value: bool | None = None

    def _data(self) -> dict:
        return self._car_store()

    def _car_charging(self) -> bool | None:
        raw = self._data().get("charging")
        if isinstance(raw, bool):
            return raw
        return self._last_car_value

    async def async_added_to_hass(self) -> None:
        raw = self._data().get("charging")
        if isinstance(raw, bool):
            self._attr_is_on = raw
            self._last_car_value = raw
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_UPDATE}_{self._entry.entry_id}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        raw = self._data().get("charging")
        if not isinstance(raw, bool):
            self.async_write_ha_state()
            return

        if self._pending_ha_target is not None:
            if raw == self._pending_ha_target:
                self._pending_ha_target = None
                self._pending_car_value = None
            elif (
                self._pending_car_value is not None
                and raw != self._pending_car_value
            ):
                self._pending_ha_target = None
                self._pending_car_value = None
            else:
                self.async_write_ha_state()
                return

        if self._attr_is_on != raw:
            self._attr_is_on = raw
        self._last_car_value = raw
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self._pending_ha_target = True
        self._pending_car_value = self._car_charging()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self._pending_ha_target = False
        self._pending_car_value = self._car_charging()
        self.async_write_ha_state()
