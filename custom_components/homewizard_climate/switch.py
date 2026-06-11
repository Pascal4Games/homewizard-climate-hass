"""Switch platform for homewizard_climate."""
import logging

from homewizard_climate_ws.model.climate_device_state import (
    HomeWizardClimateDeviceState,
)
from homewizard_climate_ws.model.climate_device import (
    HomeWizardClimateDeviceType,
)
from homewizard_climate_ws.ws.hw_websocket import HomeWizardClimateWebSocket

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create switch entries for Dehumidifier lock."""
    websockets = hass.data[DOMAIN][entry.entry_id]["websockets"]

    entities = [
        HomeWizardLockSwitchEntity(ws, hass)
        for ws in websockets
        if ws.device.type == HomeWizardClimateDeviceType.DEHUMIDIFIER
    ]
    async_add_entities(entities)


class HomeWizardLockSwitchEntity(SwitchEntity):
    """Lock switch for a HomeWizard Dehumidifier."""

    def __init__(
        self, device_web_socket: HomeWizardClimateWebSocket, hass: HomeAssistant
    ) -> None:
        """Initialize the switch."""
        self._device_web_socket = device_web_socket
        self._device_web_socket.set_on_state_change(self.on_device_state_change)
        self._hass = hass
        self._logger = logging.getLogger(
            f"{__name__}.{self._device_web_socket.device.identifier}"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_web_socket.device.identifier)},
            name=self._device_web_socket.device.name,
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this switch."""
        return (
            f"{self._device_web_socket.device.type}"
            f"_{self._device_web_socket.device.identifier}_lock"
        )

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"{self._device_web_socket.device.name} Beveiliging"

    @property
    def is_on(self) -> bool:
        """Return true if lock is on."""
        return self._device_web_socket.last_state.lock

    def turn_on(self, **kwargs) -> None:
        """Turn on the lock."""
        self._device_web_socket.turn_on_lock()

    def turn_off(self, **kwargs) -> None:
        """Turn off the lock."""
        self._device_web_socket.turn_off_lock()

    def _dispatch(self, state: HomeWizardClimateDeviceState, diff: str) -> None:
        """Call all registered callbacks."""
        for callback in self._callbacks:
            callback(state, diff)

    def on_device_state_change(
        self, state: HomeWizardClimateDeviceState, diff: str
    ) -> None:
        """Get called when any update is pushed through the websocket server and updates HA state."""
        self._logger.debug("on_device_state_change aangeroepen: %s", diff)
        self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)
