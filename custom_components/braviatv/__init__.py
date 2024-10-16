"""Support for interface with a Sony Bravia TV."""
from __future__ import annotations

from datetime import timedelta
import async_timeout
import logging

from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .client import SonyBraviaClient, SonyBraviaException
from .client.device import SonyBraviaDevice
from .const import (
    DATA_COORDINATOR,
    CONF_EXT_SPEAKER,
    CONF_PSK,
    CONF_SAVE_RESPONSES,
    CONF_SOURCE_CONFIG,
    CONF_TIME_FORMAT,
    CONF_TIMEOUT,
    DEFAULT_EXT_SPEAKER,
    DEFAULT_SAVE_LOCATION,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOURCE_CONFIG,
    DEFAULT_TIME_FORMAT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MANUFACTURER,
    UNDO_UPDATE_LISTENER,
)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.REMOTE]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up HomeKit from a config entry."""
    data = config_entry.data
    options = config_entry.options

    conf_save_responses = options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
    conf_scan_interval = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    conf_timeout = options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

    conf_save_location = DEFAULT_SAVE_LOCATION if conf_save_responses else None

    client = SonyBraviaClient(host=data[CONF_HOST], psk=data[CONF_PSK], save_location=conf_save_location)

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with async_timeout.timeout(conf_timeout):
                return await hass.async_add_executor_job(client.update)
        except SonyBraviaException as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}")

    coordinator = DataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"Sony BRAVIA ({data[CONF_HOST]})",
        update_method=async_update_data,
        update_interval=timedelta(seconds=conf_scan_interval),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        CONF_EXT_SPEAKER: options.get(CONF_EXT_SPEAKER, data.get(CONF_EXT_SPEAKER, DEFAULT_EXT_SPEAKER)),
        CONF_SOURCE_CONFIG: options.get(CONF_SOURCE_CONFIG, data.get(CONF_SOURCE_CONFIG, DEFAULT_SOURCE_CONFIG)),
        CONF_TIME_FORMAT: options.get(CONF_TIME_FORMAT, data.get(CONF_TIME_FORMAT, DEFAULT_TIME_FORMAT)),
        DATA_COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: config_entry.add_update_listener(async_update_listener),
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class SonyBraviaEntity(CoordinatorEntity):
    """Representation of a Sony BRAVIA device."""

    def __init__(self, coordinator: DataUpdateCoordinator):
        """Initialize device."""
        super().__init__(coordinator)

    @property
    def device(self) -> SonyBraviaDevice | None:
        """Return information about the device."""
        return self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return information about the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.serial)},
            manufacturer=MANUFACTURER,
            model=self.device.model,
            name=self.device.name,
            sw_version=self.device.interface_version,
            hw_version=self.device.serial,
        )

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return f"{MANUFACTURER} {self.device.name} {self.device.model}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._unique_id
