"""Component to interface with various media players."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.components.media_player import (
    DOMAIN as DOMAIN_MEDIA_PLAYER,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_APP,
    MEDIA_TYPE_TVSHOW,
    MEDIA_TYPE_VIDEO,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import SonyBraviaEntity
from .const import (
    ATTR_APP,
    ATTR_APP_LIST,
    ATTR_COMMAND,
    ATTR_COMMAND_LIST,
    DATA_COORDINATOR,
    CONF_12H,
    CONF_EXT_SPEAKER,
    CONF_SOURCE,
    CONF_SOURCE_CONFIG,
    CONF_TIME_FORMAT,
    DOMAIN,
    SERVICE_OPEN_APP,
    SERVICE_SEND_COMMAND,
    SOURCE_APP,
)

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.PAUSE |
    MediaPlayerEntityFeature.VOLUME_STEP |
    MediaPlayerEntityFeature.VOLUME_MUTE |
    MediaPlayerEntityFeature.VOLUME_SET |
    MediaPlayerEntityFeature.PREVIOUS_TRACK |
    MediaPlayerEntityFeature.NEXT_TRACK |
    MediaPlayerEntityFeature.TURN_ON |
    MediaPlayerEntityFeature.TURN_OFF |
    MediaPlayerEntityFeature.SELECT_SOURCE |
    MediaPlayerEntityFeature.PLAY |
    MediaPlayerEntityFeature.STOP
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: entity_platform.AddEntitiesCallback) -> None:
    """Set up a Sony BRAVIA media player entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    ext_speaker = entry[CONF_EXT_SPEAKER]
    source_config = entry[CONF_SOURCE_CONFIG]
    time_format = entry[CONF_TIME_FORMAT]

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_OPEN_APP,
        {
            vol.Required(ATTR_APP): cv.string,
        },
        "open_app",
    )
    platform.async_register_entity_service(
        SERVICE_SEND_COMMAND,
        {
            vol.Required(ATTR_COMMAND): cv.string,
        },
        "send_command",
    )

    async_add_entities([SonyBraviaTelevision(coordinator, ext_speaker, source_config, time_format)], True)


class SonyBraviaTelevision(MediaPlayerEntity, SonyBraviaEntity):
    """Representation of a Sony TV."""

    def __init__(self, coordinator: DataUpdateCoordinator, ext_speaker: bool, source_config: Mapping[str, str], time_format: str):
        """Initialize device."""
        super().__init__(coordinator)
        self._app_icon = None
        self._app_title = None
        self._ext_speaker = ext_speaker
        self._playing = False
        self._source_config = source_config
        self._time_format = time_format
        self._unique_id = f"{self.device.serial}-{DOMAIN_MEDIA_PLAYER}"

    @property
    def conf_sources(self) -> Mapping[str, str] | None:
        """List of available input sources."""
        return self._apply_source_config(self.device.sources)

    @property
    def conf_title(self) -> str | None:
        """Name of the current running app."""
        return self._apply_source_config_name(self.device.title)

    def _apply_source_config(self, sources: Mapping[str, str]) -> Mapping[str, str] | None:
        if self._source_config:
            conf_sources = {}
            for source, uri in sources.items():
                if source in [conf[CONF_SOURCE] for conf in self._source_config]:
                    name = self._apply_source_config_name(source)
                    conf_sources[name] = uri
            return conf_sources
        return sources

    def _apply_source_config_name(self, source: str) -> str | None:
        for conf in self._source_config:
            if conf[CONF_SOURCE] == source:
                return conf[CONF_NAME]
        return source

    def _apply_time_format(self, raw_time: str) -> str | None:
        """Convert time format."""
        if self._time_format == CONF_12H:
            hours, minutes = raw_time.split(":")
            hours, minutes = int(hours), int(minutes)
            setting = "AM"
            if hours >= 12:
                setting = "PM"
                if hours > 12:
                    hours -= 12
            elif hours == 0:
                hours = 12
            return "{}:{:02d} {}".format(hours, minutes, setting)
#            return f"{hours}:{minutes} {setting}"
        return raw_time

    def _reset_app_info(self) -> None:
        """Convert time format."""
        self._app_icon = None
        self._app_title = None

    @property
    def device_class(self) -> MediaPlayerDeviceClass | str | None:
        """Return the class of this entity."""
        return MediaPlayerDeviceClass.TV

    @property
    def is_volume_muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
        return self.device.mute

    @property
    def media_content_id(self) -> str | None:
        """Content ID of current playing media."""
        if self.conf_title:
            return self.conf_title
        return SOURCE_APP

    @property
    def media_content_type(self) -> str | None:
        """Content type of current playing media."""
        if self.conf_title:
            self._reset_app_info()
            if self.device.tv_input_active:
                return MEDIA_TYPE_TVSHOW
            return MEDIA_TYPE_VIDEO
        return MEDIA_TYPE_APP

    @property
    def app_id(self) -> str | None:
        """ID of the current running app."""
        if self._app_title:
            return self._app_title
        elif self.conf_title:
            return None
        return SOURCE_APP

    @property
    def app_name(self) -> str | None:
        """Name of the current running app."""
        if self._app_title:
            return self._app_title
        elif self.conf_title:
            return None
        return SOURCE_APP

    @property
    def media_image_url(self) -> str | None:
        """Image url of current playing media."""
        return self._app_icon

    @property
    def media_channel(self) -> str | None:
        """Channel currently playing."""
        if self.device.display_number:
            return self.device.display_number
        return None

    @property
    def media_series_title(self) -> str | None:
        """Title of series of current playing media, TV show only."""
        if self.device.program_title:
            if self.device.start_time and self.device.end_time:
                start_time = self._apply_time_format(self.device.start_time)
                end_time = self._apply_time_format(self.device.end_time)
                return f"{self.device.program_title} | {start_time} - {end_time}"
            return self.device.program_title
        return None

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        if self.conf_title:
            if self.device.display_number:
                return f"{self.device.display_number}: {self.conf_title}"
            return self.conf_title
        return None

    @property
    def source(self) -> str | None:
        """Name of the current input source."""
        if self._app_title:
            return self._app_title
        elif self.conf_title:
            return self.conf_title
        return SOURCE_APP

    @property
    def source_list(self) -> list[str] | None:
        """List of available input sources."""
        return list(self.conf_sources.keys())

    @property
    def state(self) -> str | None:
        """State of the player."""
        return STATE_ON if self.device.is_on else STATE_OFF

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = super().state_attributes
        if not attrs:
            attrs = {}

        if self.device.is_on:
            if self.device.apps:
                attrs[ATTR_APP_LIST] = sorted(list(self.device.apps.keys()))

            if self.device.commands:
                attrs[ATTR_COMMAND_LIST] = sorted(list(self.device.commands.keys()))

        return attrs

    @property
    def supported_features(self) -> int | None:
        """Flag media player features that are supported."""
        if self._ext_speaker:
            return SUPPORTED_FEATURES ^ MediaPlayerEntityFeature.VOLUME_SET
        return SUPPORTED_FEATURES

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        if self.device.volume:
            return int(self.device.volume) / 100
        return None

    def set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        volume = str(int(round(volume * 100)))
        setattr(self.device, "volume_level", volume)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await super().async_set_volume_level(volume)
        await self.coordinator.async_request_refresh()

    def turn_on(self) -> None:
        """Turn the media player on."""
        setattr(self.device, "power_status", True)
        self._reset_app_info()

    async def async_turn_on(self, **kwargs) -> None:
        await super().async_turn_on()
        await self.coordinator.async_request_refresh()

    def turn_off(self) -> None:
        """Turn the media player off."""
        setattr(self.device, "power_status", False)
        self._reset_app_info()

    async def async_turn_off(self, **kwargs) -> None:
        await super().async_turn_off()
        await self.coordinator.async_request_refresh()

    def volume_up(self) -> None:
        """Turn volume up for media player."""
        self.device.send_command(self.device.commands["VolumeUp"])

    def volume_down(self) -> None:
        """Turn volume down for media player."""
        self.device.send_command(self.device.commands["VolumeDown"])

    def mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        setattr(self.device, "mute", bool(mute))

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        await super().async_mute_volume(mute)
        await self.coordinator.async_request_refresh()

    def select_source(self, source: str) -> None:
        """Select input source."""
        if source in list(self.conf_sources.keys()):
            self.device.set_play_content(self.conf_sources[source])
            self._reset_app_info()

    def media_play(self) -> None:
        """Send play command."""
        self.device.send_command(self.device.commands["Play"])
        self._playing = True

    def media_pause(self) -> None:
        """Send pause command."""
        command = "TvPause" if self.device.tv_input_active else "Pause"
        self.device.send_command(self.device.commands[command])
        self._playing = False

    def media_stop(self) -> None:
        """Send stop command."""
        self.device.send_command(self.device.commands["Stop"])
        self._playing = False

    def media_next_track(self) -> None:
        """Send next track command."""
        command = "ChannelUp" if self.device.tv_input_active else "Next"
        self.device.send_command(self.device.commands[command])

    def media_previous_track(self) -> None:
        """Send previous track command."""
        command = "ChannelDown" if self.device.tv_input_active else "Prev"
        self.device.send_command(self.device.commands[command])

    def open_app(self, app: str) -> None:
        """Open an app on the media player."""
        if self.device.is_on and app in list(self.device.apps.keys()):
            self.device.set_active_app(self.device.apps[app]["uri"])
            self._app_icon = self.device.apps[app].get("icon")
            self._app_title = app

    def send_command(self, command: str) -> None:
        """Send a command to the media player."""
        self.device.send_command(self.device.commands[command])
