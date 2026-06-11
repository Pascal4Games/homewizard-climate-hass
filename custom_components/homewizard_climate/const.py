"""Constants for the Homewizard Climate integration."""

from homeassistant.const import Platform

DOMAIN = "homewizard_climate"
PLATFORMS = [Platform.CLIMATE, Platform.FAN, Platform.HUMIDIFIER, Platform.SENSOR, Platform.SWITCH]
