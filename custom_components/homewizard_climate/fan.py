"""Fan platform for homewizard_climate."""
import logging
import time

from homewizard_climate_ws.model.climate_device_state import (
    HomeWizardClimateDeviceState,
)
from homewizard_climate_ws.model.climate_device import (
    HomeWizardClimateDeviceType,
)
from homewizard_climate_ws.ws.hw_websocket import HomeWizardClimateWebSocket

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN

ORDERED_NAMED_FAN_SPEEDS = [1, 2, 3]  # off is not included


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create entries for each FAN device in Homewizard cloud."""
    websockets = hass.data[DOMAIN][entry.entry_id]["websockets"]

    fan_websockets = [
        ws for ws in websockets if ws.device.type == HomeWizardClimateDeviceType.FAN
    ]

    entities = [HomeWizardFanEntity(ws, hass) for ws in fan_websockets]
    async_add_entities(entities)


class HomeWizardFanEntity(FanEntity):
    """Fan entity for a given device in Homewizard cloud."""

    def __init__(
        self, device_web_socket: HomeWizardClimateWebSocket, hass: HomeAssistant
    ) -> None:
        """Initialize the device and identifiers."""
        self._device_web_socket = device_web_socket
        self._device_web_socket.set_on_state_change(self.on_device_state_change)
        self._hass = hass
        self._enable_turn_on_off_backwards_compatibility = False
        # FIX: _logger was missing, causing AttributeError in on_device_state_change
        self._logger = logging.getLogger(
            f"{__name__}.{self._device_web_socket.device.identifier}"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_web_socket.device.identifier)},
            name=self.name,
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"{self._device_web_socket.device.type}_{self._device_web_socket.device.identifier}"

    @property
    def name(self) -> str:
        """Return the name of the fan device."""
        return self._device_web_socket.device.name

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on."""
        return self._device_web_socket.last_state.power_on

    @property
    def supported_features(self) -> FanEntityFeature:
        """Return supported features."""
        return (
            FanEntityFeature.OSCILLATE
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.SET_SPEED
        )

    @property
    def oscillating(self) -> bool:
        """Return whether oscillation is on."""
        return self._device_web_socket.last_state.oscillation

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        current_speed = self._device_web_socket.last_state.speed
        if current_speed is None:
            return None
        return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, current_speed)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    def oscillate(self, oscillating: bool) -> None:
        """Oscillate the fan."""
        if oscillating:
            self._device_web_socket.turn_on_oscillation()
        else:
            self._device_web_socket.turn_off_oscillation()

    def turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs) -> None:
        """Turn on the fan."""
        self._device_web_socket.turn_on()
        if percentage is not None:
            self.set_percentage(percentage)

    def turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        self._device_web_socket.turn_off()

    def set_percentage(self, percentage: int) -> None:
        """Set the fan speed by percentage."""
        if percentage == 0:
            self._device_web_socket.turn_off()
        else:
            named_speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
            if not self._device_web_socket.last_state.power_on:
                self._device_web_socket.turn_on()
                time.sleep(0.2)
            self._device_web_socket.set_speed(named_speed)

    def _dispatch(self, state: HomeWizardClimateDeviceState, diff: str) -> None:
        """Call all registered callbacks."""
        for callback in self._callbacks:
            callback(state, diff)

    def on_device_state_change(
        self, state: HomeWizardClimateDeviceState, diff: str
    ) -> None:
        """Handle state updates pushed via the websocket."""
        self._logger.debug("on_device_state_change aangeroepen: %s", diff)
        self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)
