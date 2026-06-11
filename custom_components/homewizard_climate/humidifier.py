"""Humidifier platform for homewizard_climate (Dehumidifier)."""
import logging

from homewizard_climate_ws.model.climate_device_state import (
    HomeWizardClimateDeviceState,
)
from homewizard_climate_ws.model.climate_device import (
    HomeWizardClimateDeviceType,
)
from homewizard_climate_ws.ws.hw_websocket import HomeWizardClimateWebSocket

from homeassistant.components.humidifier import (
    HumidifierAction,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

DEHUMID_MODES = ["dehumidify", "fan", "laundry", "continuous", "automatic"]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create humidifier entries for each Dehumidifier in Homewizard cloud."""
    websockets = hass.data[DOMAIN][entry.entry_id]["websockets"]

    entities = [
        HomeWizardDehumidifierEntity(ws, hass)
        for ws in websockets
        if ws.device.type == HomeWizardClimateDeviceType.DEHUMIDIFIER
    ]
    async_add_entities(entities)


class HomeWizardDehumidifierEntity(HumidifierEntity):
    """Dehumidifier entity for a HomeWizard device."""

    _attr_device_class = HumidifierDeviceClass.DEHUMIDIFIER
    _attr_min_humidity = 30
    _attr_max_humidity = 80

    def __init__(
        self, device_web_socket: HomeWizardClimateWebSocket, hass: HomeAssistant
    ) -> None:
        """Initialize the dehumidifier entity."""
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
            name=self.name,
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this entity."""
        return (
            f"{self._device_web_socket.device.type}"
            f"_{self._device_web_socket.device.identifier}"
        )

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device_web_socket.device.name

    @property
    def is_on(self) -> bool:
        """Return true if the dehumidifier is on."""
        return self._device_web_socket.last_state.power_on

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        return self._device_web_socket.last_state.current_humidity

    @property
    def target_humidity(self) -> int | None:
        """Return the target humidity."""
        return self._device_web_socket.last_state.target_humidity

    @property
    def action(self) -> HumidifierAction | None:
        """Return the current action."""
        if not self._device_web_socket.last_state.power_on:
            return HumidifierAction.OFF
        current = self._device_web_socket.last_state.current_humidity
        target = self._device_web_socket.last_state.target_humidity
        if current is not None and target is not None and current <= target:
            return HumidifierAction.IDLE
        return HumidifierAction.DRYING

    @property
    def supported_features(self) -> HumidifierEntityFeature:
        """Return supported features."""
        return HumidifierEntityFeature.MODES

    @property
    def available_modes(self) -> list[str]:
        """Return available modes."""
        return DEHUMID_MODES

    @property
    def mode(self) -> str | None:
        """Return current mode."""
        return self._device_web_socket.last_state.mode

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        fault = self._device_web_socket.last_state.fault
        return {
            "fout_status": fault.strip("[]'\"").replace("_", " ").title() if fault else "Geen fout",
        }

    def turn_on(self, **kwargs) -> None:
        """Turn on the dehumidifier."""
        self._device_web_socket.turn_on()

    def turn_off(self, **kwargs) -> None:
        """Turn off the dehumidifier."""
        self._device_web_socket.turn_off()

    def set_humidity(self, humidity: int) -> None:
        """Set the target humidity."""
        self._device_web_socket.set_target_humidity(humidity)

    def set_mode(self, mode: str) -> None:
        """Set the mode."""
        self._device_web_socket.set_mode(mode)

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
