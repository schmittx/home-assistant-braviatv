"""Support to interface with universal remote control devices."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, final

from homeassistant.components.remote import DOMAIN as DOMAIN_REMOTE, RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import SonyBraviaEntity
from .const import (
    ATTR_COMMAND_LIST,
    DATA_COORDINATOR,
    DOMAIN,
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up a Sony BRAVIA remote entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]

    async_add_entities([SonyBraviaRemote(coordinator)], True)


class SonyBraviaRemote(RemoteEntity, SonyBraviaEntity):
    """Device that sends commands to a Sony TV."""

    def __init__(self, coordinator: DataUpdateCoordinator):
        """Initialize device."""
        super().__init__(coordinator)
        self._unique_id = f"{self.device.serial}-{DOMAIN_REMOTE}"

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self.device.is_on

    @final
    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = super().state_attributes
        if not attrs:
            attrs = {}

        if self.device.is_on and self.device.commands:
            attrs[ATTR_COMMAND_LIST] = sorted(list(self.device.commands.keys()))

        return attrs

    def send_command(self, commands: Iterable[str], **kwargs: Any) -> None:
        """Send commands to a device."""
        for command in commands:
            self.device.send_command(command)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        setattr(self.device, "power_status", True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on()
        await self.coordinator.async_request_refresh()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        setattr(self.device, "power_status", False)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off()
        await self.coordinator.async_request_refresh()
