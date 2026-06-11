"""The Homewizard Climate integration."""
from __future__ import annotations

import logging
from typing import Callable

from homewizard_climate_ws.api.api import (
    HomeWizardClimateApi,
    InvalidHomewizardAuth,
)
from homewizard_climate_ws.model.climate_device import HomeWizardClimateDevice
from homewizard_climate_ws.model.climate_device_state import HomeWizardClimateDeviceState
from homewizard_climate_ws.ws.hw_websocket import HomeWizardClimateWebSocket

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


class MultiCallbackWebSocket:
    def __init__(self, websocket: HomeWizardClimateWebSocket) -> None:
        self._websocket = websocket
        self._callbacks: list[Callable] = []
        self._websocket.set_on_state_change(self._dispatch)

    def _dispatch(self, state: HomeWizardClimateDeviceState, diff: str) -> None:
        for callback in self._callbacks:
            callback(state, diff)

    def set_on_state_change(self, callback: Callable) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    @property
    def device(self):
        return self._websocket.device

    @property
    def last_state(self):
        return self._websocket.last_state

    def disconnect(self):
        return self._websocket.disconnect()

    def connect_in_thread(self):
        return self._websocket.connect_in_thread()

    def __getattr__(self, name):
        return getattr(self._websocket, name)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Homewizard Climate from a config entry."""

    api: HomeWizardClimateApi = HomeWizardClimateApi(
        entry.data.get(CONF_USERNAME), entry.data.get(CONF_PASSWORD)
    )

    try:
        await hass.async_add_executor_job(api.login)
    except InvalidHomewizardAuth as exc:
        raise ConfigEntryAuthFailed from exc

    devices: list[HomeWizardClimateDevice] = await hass.async_add_executor_job(
        api.get_devices
    )

    websockets = []
    for device in devices:
        websocket = HomeWizardClimateWebSocket(api, device)
        websockets.append(MultiCallbackWebSocket(websocket))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id]["websockets"] = websockets

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Nu pas verbinden, zodat alle callbacks al geregistreerd zijn
    for ws in websockets:
        ws.connect_in_thread()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    for websocket in hass.data[DOMAIN][entry.entry_id]["websockets"]:
        websocket.disconnect()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
