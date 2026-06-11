"""Sensor platform for homewizard_climate."""
import logging

from homewizard_climate_ws.model.climate_device_state import (
    HomeWizardClimateDeviceState,
)
from homewizard_climate_ws.model.climate_device import (
    HomeWizardClimateDeviceType,
)
from homewizard_climate_ws.ws.hw_websocket import HomeWizardClimateWebSocket

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create sensor entries for each device in Homewizard cloud."""
    websockets = hass.data[DOMAIN][entry.entry_id]["websockets"]

    entities: list[SensorEntity] = []
    for ws in websockets:

        # Fault sensor: DEHUMIDIFIER én AIRCOOLER
        if ws.device.type in (
            HomeWizardClimateDeviceType.DEHUMIDIFIER,
            HomeWizardClimateDeviceType.AIRCOOLER,
        ):
            entities.append(HomeWizardFaultSensorEntity(ws, hass))

    async_add_entities(entities)

class HomeWizardFaultSensorEntity(SensorEntity):
    """Fault/error status sensor for a HomeWizard AirCooler."""

    def __init__(
        self, device_web_socket: HomeWizardClimateWebSocket, hass: HomeAssistant
    ) -> None:
        """Initialize the fault sensor."""
        self._device_web_socket = device_web_socket
        self._device_web_socket.set_on_state_change(self.on_device_state_change)
        self._hass = hass
        self._logger = logging.getLogger(
            f"{__name__}.{self._device_web_socket.device.identifier}.fault"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Link this sensor to the same device as the climate entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_web_socket.device.identifier)},
            name=self._device_web_socket.device.name,
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for the fault sensor."""
        return (
            f"{self._device_web_socket.device.type}"
            f"_{self._device_web_socket.device.identifier}_fault"
        )

    @property
    def name(self) -> str:
        """Return the sensor name."""
        return f"{self._device_web_socket.device.name} Fout status"

    @property
    def native_value(self) -> str:
        """Return active error codes, or 'Geen fout'."""
        if self._device_web_socket.device.type == HomeWizardClimateDeviceType.AIRCOOLER:
            warning = self._device_web_socket.last_state.warning
            value = warning.strip("[]'\"").replace("_", " ").title() if warning else ""
        else:
            fault = self._device_web_socket.last_state.fault
            value = fault.strip("[]'\"").replace("_", " ").title() if fault else ""
        return value if value else "Geen fout"

    @property
    def icon(self) -> str:
        """Return an icon that reflects the fault state."""
        if self._device_web_socket.device.type == HomeWizardClimateDeviceType.AIRCOOLER:
            codes = self._device_web_socket.last_state.warning or []
        else:
            codes = self._device_web_socket.last_state.fault or []
        if not codes:
            return "mdi:check-circle-outline"
        return "mdi:alert-circle-outline"

    def _dispatch(self, state: HomeWizardClimateDeviceState, diff: str) -> None:
        """Call all registered callbacks."""
        for callback in self._callbacks:
            callback(state, diff)

    def on_device_state_change(
        self, state: HomeWizardClimateDeviceState, diff: str
    ) -> None:
        """Handle state updates from the websocket."""
        self._logger.debug("on_device_state_change aangeroepen: %s", diff)
        self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)
