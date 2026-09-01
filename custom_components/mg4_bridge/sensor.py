from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_NAME, CONF_PREFIX, DOMAIN, SIGNAL_UPDATE
from .device import bridge_device
from .command_feedback import localize_command, localize_detail

# key, unit, device_class, state_class, suggested_display_precision
SENSORS: tuple[
    tuple[str, str | None, SensorDeviceClass | None, SensorStateClass | None, int | None],
    ...,
] = (
    ("last_update", None, SensorDeviceClass.TIMESTAMP, None, None),
    ("update_reason", None, None, None, None),
    ("vehicle_last_run", None, SensorDeviceClass.TIMESTAMP, None, None),
    ("command_feedback", None, None, None, None),
    ("address", None, None, None, None),
    ("mileage", UnitOfLength.KILOMETERS, SensorDeviceClass.DISTANCE, SensorStateClass.TOTAL_INCREASING, 0),
    ("battery", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, 1),
    ("range", UnitOfLength.KILOMETERS, SensorDeviceClass.DISTANCE, SensorStateClass.MEASUREMENT, 0),
    ("exterior_temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, 0),
    ("tire_pressure_fl", UnitOfPressure.KPA, SensorDeviceClass.PRESSURE, SensorStateClass.MEASUREMENT, 0),
    ("tire_pressure_fr", UnitOfPressure.KPA, SensorDeviceClass.PRESSURE, SensorStateClass.MEASUREMENT, 0),
    ("tire_pressure_rl", UnitOfPressure.KPA, SensorDeviceClass.PRESSURE, SensorStateClass.MEASUREMENT, 0),
    ("tire_pressure_rr", UnitOfPressure.KPA, SensorDeviceClass.PRESSURE, SensorStateClass.MEASUREMENT, 0),
    ("charging_status", None, None, None, None),
    ("charge_remaining", UnitOfTime.MINUTES, SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT, 0),
    ("charge_finish", None, SensorDeviceClass.TIMESTAMP, None, None),
    ("battery_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, 2),
    ("battery_current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, 2),
    ("battery_charging_power", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, 2),
    ("station_dc_current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, 2),
    ("station_dc_power", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, 2),
    ("ac_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, 0),
    ("ac_current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, 1),
    ("ac_charging_power", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, 2),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    prefix = entry.data[CONF_PREFIX]
    name = entry.data[CONF_NAME]
    async_add_entities(
        [Mg4Sensor(hass, entry, prefix, name, *item) for item in SENSORS]
    )


class Mg4Sensor(RestoreSensor):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        prefix: str,
        device_name: str,
        key: str,
        unit,
        device_class,
        state_class,
        precision: int | None,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._key = key
        self._attr_unique_id = f"{prefix}_{key}"
        self._attr_translation_key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_suggested_display_precision = precision
        self._attr_device_info = bridge_device(prefix, device_name)
        if key == "charging_status":
            self._attr_icon = "mdi:ev-station"
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = [
                "unplugged",
                "AC",
                "connecting",
                "plugged_in",
                "stopped",
                "DC",
                "unknown",
            ]
        if key == "address":
            self._attr_icon = "mdi:map-marker"
        if key == "vehicle_last_run":
            self._attr_icon = "mdi:clock-outline"
        if key == "command_feedback":
            self._attr_icon = "mdi:message-reply-text"
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = ["idle", "ok", "fail"]
        if key == "update_reason":
            self._attr_icon = "mdi:history"
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = [
                "periodic",
                "startup",
                "wifi",
                "vehicle_ready",
                "car_changed",
                "ha_command",
                "manual",
                "retry",
                "unknown",
            ]

    def _data(self) -> dict:
        return self.hass.data[DOMAIN][self._entry.entry_id]["data"]

    @property
    def native_value(self):
        val = self._data().get(self._key)
        if self._key == "last_update" and isinstance(val, str):
            parsed = dt_util.parse_datetime(val)
            return parsed if parsed is not None else val
        if self._key == "vehicle_last_run" and isinstance(val, str):
            parsed = dt_util.parse_datetime(val)
            return parsed if parsed is not None else val
        if self._key == "charge_finish" and isinstance(val, str):
            parsed = dt_util.parse_datetime(val)
            return parsed if parsed is not None else val
        if isinstance(val, datetime):
            return val
        if self._key == "charging_status" and isinstance(val, str):
            opts = self._attr_options or []
            if val in opts:
                return val
            return "unknown"
        if self._key == "command_feedback":
            val = self._data().get(self._key)
            if not isinstance(val, str) or val not in (self._attr_options or []):
                return "idle"
            return val
        if self._key == "update_reason":
            val = self._data().get(self._key)
            opts = self._attr_options or []
            if isinstance(val, str) and val in opts:
                return val
            if isinstance(val, str) and val:
                return "unknown"
            return None
        return val

    @property
    def extra_state_attributes(self):
        if self._key == "charging_status":
            raw = self._data().get(self._key)
            if isinstance(raw, str) and raw not in (self._attr_options or []):
                return {"raw_status": raw}
            return None
        if self._key == "command_feedback":
            data = self._data()
            attrs: dict = {}
            cmd = data.get("command_name")
            if cmd:
                attrs["command"] = cmd
                label = localize_command(self.hass, str(cmd))
                if label:
                    attrs["command_label"] = label
            key = data.get("command_detail_key")
            arg = data.get("command_detail_arg")
            if key:
                attrs["detail_key"] = key
                if arg:
                    attrs["detail_arg"] = arg
                detail = localize_detail(
                    self.hass,
                    str(key),
                    str(arg) if arg is not None else None,
                )
                if detail:
                    attrs["detail"] = detail
            at = data.get("command_at")
            if isinstance(at, str):
                parsed = dt_util.parse_datetime(at)
                attrs["at"] = parsed.isoformat() if parsed is not None else at
            return attrs or None
        return None

    @property
    def available(self) -> bool:
        data = self._data()
        if not data or data.get("online") is False:
            return False
        if self._key == "charge_finish":
            return self._key in data and data.get("charge_remaining", 0) not in (0, None)
        if self._key == "address":
            return self._key in data and bool(data.get("address"))
        if self._key == "command_feedback":
            return True
        return self._key in data

    async def async_added_to_hass(self) -> None:
        last = await self.async_get_last_sensor_data()
        if last is not None and last.native_value is not None:
            data = self._data()
            if self._key not in data:
                data[self._key] = last.native_value
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{SIGNAL_UPDATE}_{self._entry.entry_id}", self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
