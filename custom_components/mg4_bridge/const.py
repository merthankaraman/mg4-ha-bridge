from typing import Final

DOMAIN = "mg4_bridge"
SIGNAL_UPDATE = "mg4_bridge_update"
CONF_PREFIX = "prefix"
CONF_NAME = "name"
DEFAULT_PREFIX = "mg4"
DEFAULT_NAME = "MG4"
SERVICE_PUSH = "push"

# English entity names (default). Turkish via translations/tr.json + translation_key.
ENTITY_SENSOR_NAMES: Final[dict[str, str]] = {
    "last_update": "Last update",
    "address": "Address",
    "mileage": "Odometer",
    "battery": "State of charge",
    "range": "Range",
    "exterior_temperature": "Exterior temperature",
    "tire_pressure_fl": "Tire front left",
    "tire_pressure_fr": "Tire front right",
    "tire_pressure_rl": "Tire rear left",
    "tire_pressure_rr": "Tire rear right",
    "charging_status": "Charging status",
    "charge_remaining": "Charge remaining",
    "charge_finish": "Charge finish time",
    "battery_voltage": "Battery voltage",
    "battery_current": "Battery current",
    "battery_charging_power": "Battery power",
    "station_dc_current": "Station current",
    "station_dc_power": "Station power",
    "ac_voltage": "AC voltage",
    "ac_current": "AC current",
    "ac_charging_power": "AC charge power",
}

ENTITY_BINARY_SENSOR_NAMES: Final[dict[str, str]] = {
    "charging": "Charging",
}

ENTITY_SWITCH_NAMES: Final[dict[str, str]] = {
    "hvac": "Climate",
}

ENTITY_NUMBER_NAMES: Final[dict[str, str]] = {
    "charge_limit_set": "Charge limit",
}

ENTITY_DEVICE_TRACKER_NAMES: Final[dict[str, str]] = {
    "location": "Location",
}
