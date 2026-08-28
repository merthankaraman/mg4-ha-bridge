from __future__ import annotations

from datetime import datetime

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_NAME, CONF_PREFIX, DOMAIN, ENTITY_NUMBER_NAMES, SIGNAL_UPDATE
from .device import bridge_device

# Araç ham değer 1..7 → %40..%100 (40 + (n-1)*10)
CHARGE_LIMIT_MIN = 40
CHARGE_LIMIT_MAX = 100
CHARGE_LIMIT_STEP = 10
# HA slider → poll → araç onaylanana kadar eski push ile geri yazma
PENDING_HA_GRACE_SEC = 90


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
    entity = Mg4ChargeLimitNumber(hass, entry)
    entity.entity_id = f"number.{prefix}_charge_limit"
    async_add_entities([entity])


class Mg4ChargeLimitNumber(NumberEntity):
    """Araba → HA: push ile slider senkron; HA → araba: poll hedefi uygular."""

    _attr_has_entity_name = True
    _attr_translation_key = "charge_limit_set"
    _attr_name = ENTITY_NUMBER_NAMES["charge_limit_set"]
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
        self._pending_since: datetime | None = None

    def _data(self) -> dict:
        return self.hass.data[DOMAIN][self._entry.entry_id]["data"]

    async def async_added_to_hass(self) -> None:
        raw = self._data().get("charge_limit")
        if raw is not None:
            pct = normalize_charge_limit_pct(raw)
            if pct is not None:
                self._attr_native_value = pct
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

        now = dt_util.utcnow()
        if self._pending_ha_target is not None:
            if int(pct) == self._pending_ha_target:
                self._pending_ha_target = None
                self._pending_since = None
            elif (
                self._pending_since is not None
                and (now - self._pending_since).total_seconds() < PENDING_HA_GRACE_SEC
            ):
                self.async_write_ha_state()
                return
            else:
                self._pending_ha_target = None
                self._pending_since = None

        if self._attr_native_value != pct:
            self._attr_native_value = pct
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        pct = normalize_charge_limit_pct(value)
        if pct is None:
            return
        self._attr_native_value = pct
        self._pending_ha_target = int(pct)
        self._pending_since = dt_util.utcnow()
        self.async_write_ha_state()
