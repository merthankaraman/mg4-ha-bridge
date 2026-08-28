from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, CONF_PREFIX, DOMAIN, SIGNAL_UPDATE
from .device import bridge_device

# Araç ham değer 1..7 → %40..%100 (40 + (n-1)*10)
CHARGE_LIMIT_MIN = 40
CHARGE_LIMIT_MAX = 100
CHARGE_LIMIT_STEP = 10


def normalize_charge_limit_pct(value: float | int) -> float | None:
    try:
        pct = int(round(float(value) / CHARGE_LIMIT_STEP) * CHARGE_LIMIT_STEP)
        pct = max(CHARGE_LIMIT_MIN, min(CHARGE_LIMIT_MAX, pct))
        return float(pct)
    except (TypeError, ValueError):
        return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    prefix = entry.data[CONF_PREFIX]
    charge = Mg4ChargeLimitNumber(hass, entry)
    charge.entity_id = f"number.{prefix}_charge_limit"
    hvac_temp = Mg4HvacTemperatureNumber(hass, entry)
    hvac_temp.entity_id = f"number.{prefix}_hvac_temperature"
    async_add_entities([charge, hvac_temp])


class Mg4ChargeLimitNumber(NumberEntity):
    """Araba → HA: push ile slider senkron; HA → araba: poll hedefi uygular."""

    _attr_has_entity_name = True
    _attr_translation_key = "charge_limit_set"
    _attr_icon = "mdi:battery-charging-80"
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = CHARGE_LIMIT_MIN
    _attr_native_max_value = CHARGE_LIMIT_MAX
    _attr_native_step = CHARGE_LIMIT_STEP
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._prefix = entry.data[CONF_PREFIX]
        self._attr_unique_id = f"{self._prefix}_charge_limit_set"
        self._attr_device_info = bridge_device(self._prefix, entry.data[CONF_NAME])
        self._attr_native_value = 80.0
        self._pending_ha_target: int | None = None
        self._pending_car_value: int | None = None
        self._last_car_value: int | None = None

    def _data(self) -> dict:
        return self.hass.data[DOMAIN][self._entry.entry_id]["data"]

    def _car_charge_limit(self) -> int | None:
        raw = self._data().get("charge_limit")
        if raw is None:
            return self._last_car_value
        pct = normalize_charge_limit_pct(raw)
        return int(pct) if pct is not None else self._last_car_value

    async def async_added_to_hass(self) -> None:
        raw = self._data().get("charge_limit")
        if raw is not None:
            pct = normalize_charge_limit_pct(raw)
            if pct is not None:
                self._attr_native_value = pct
                self._last_car_value = int(pct)
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_UPDATE}_{self._entry.entry_id}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        raw = self._data().get("charge_limit")
        if raw is None:
            self.async_write_ha_state()
            return
        pct = normalize_charge_limit_pct(raw)
        if pct is None:
            return
        car_pct = int(pct)

        if self._pending_ha_target is not None:
            if car_pct == self._pending_ha_target:
                self._pending_ha_target = None
                self._pending_car_value = None
            elif (
                self._pending_car_value is not None
                and car_pct != self._pending_car_value
            ):
                # Arabada değer değişti → hemen senkron
                self._pending_ha_target = None
                self._pending_car_value = None
            else:
                self.async_write_ha_state()
                return

        if self._attr_native_value != pct:
            self._attr_native_value = pct
        self._last_car_value = car_pct
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        pct = normalize_charge_limit_pct(value)
        if pct is None:
            return
        self._attr_native_value = pct
        self._pending_ha_target = int(pct)
        self._pending_car_value = self._car_charge_limit()
        self.async_write_ha_state()


HVAC_TEMP_MIN = 16
HVAC_TEMP_MAX = 30
HVAC_TEMP_STEP = 1


def normalize_hvac_temp_c(value: float | int) -> float | None:
    try:
        temp = int(round(float(value)))
        temp = max(HVAC_TEMP_MIN, min(HVAC_TEMP_MAX, temp))
        return float(temp)
    except (TypeError, ValueError):
        return None


class Mg4HvacTemperatureNumber(NumberEntity):
    """Araba → HA: push ile senkron; HA → araba: poll hedefi uygular."""

    _attr_has_entity_name = True
    _attr_translation_key = "hvac_temperature_set"
    _attr_icon = "mdi:thermostat"
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = float(HVAC_TEMP_MIN)
    _attr_native_max_value = float(HVAC_TEMP_MAX)
    _attr_native_step = float(HVAC_TEMP_STEP)
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._prefix = entry.data[CONF_PREFIX]
        self._attr_unique_id = f"{self._prefix}_hvac_temperature_set"
        self._attr_device_info = bridge_device(self._prefix, entry.data[CONF_NAME])
        self._attr_native_value = 22.0
        self._pending_ha_target: int | None = None
        self._pending_car_value: int | None = None
        self._last_car_value: int | None = None

    def _data(self) -> dict:
        return self.hass.data[DOMAIN][self._entry.entry_id]["data"]

    def _car_hvac_temp(self) -> int | None:
        raw = self._data().get("hvac_temp")
        if raw is None:
            return self._last_car_value
        temp = normalize_hvac_temp_c(raw)
        return int(temp) if temp is not None else self._last_car_value

    async def async_added_to_hass(self) -> None:
        raw = self._data().get("hvac_temp")
        if raw is not None:
            temp = normalize_hvac_temp_c(raw)
            if temp is not None:
                self._attr_native_value = temp
                self._last_car_value = int(temp)
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_UPDATE}_{self._entry.entry_id}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        raw = self._data().get("hvac_temp")
        if raw is None:
            self.async_write_ha_state()
            return
        temp = normalize_hvac_temp_c(raw)
        if temp is None:
            return
        car_temp = int(temp)

        if self._pending_ha_target is not None:
            if car_temp == self._pending_ha_target:
                self._pending_ha_target = None
                self._pending_car_value = None
            elif (
                self._pending_car_value is not None
                and car_temp != self._pending_car_value
            ):
                self._pending_ha_target = None
                self._pending_car_value = None
            else:
                self.async_write_ha_state()
                return

        if self._attr_native_value != temp:
            self._attr_native_value = temp
        self._last_car_value = car_temp
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        temp = normalize_hvac_temp_c(value)
        if temp is None:
            return
        self._attr_native_value = temp
        self._pending_ha_target = int(temp)
        self._pending_car_value = self._car_hvac_temp()
        self.async_write_ha_state()
