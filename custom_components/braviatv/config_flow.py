"""Config flow for the badnest component."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .client import SonyBraviaClient
from .const import (
    CONF_12H,
    CONF_24H,
    CONF_EXT_SPEAKER,
    CONF_HIDDEN,
    CONF_PSK,
    CONF_SAVE_RESPONSES,
    CONF_SOURCE,
    CONF_SOURCE_LIST,
    CONF_SOURCE_CONFIG,
    CONF_TIME_FORMAT,
    CONF_TIMEOUT,
    CONF_TITLE,
    DEFAULT_EXT_SPEAKER,
    DEFAULT_TIME_FORMAT,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    VALUES_SCAN_INTERVAL,
    VALUES_TIMEOUT,
    DATA_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)


class SonyBraviaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Total Connect config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize config flow."""
        self.client = None
        self.index = 0
        self.user_input = {}

    async def async_connect(self, host, psk):
        """Return true if the given username and password are valid."""
        self.client = SonyBraviaClient(host, psk)
        system_info = await self.hass.async_add_executor_job(self.client.get_system_info)
        if system_info:
            name, model = system_info.get("name"), system_info.get("model")
            self.user_input[CONF_TITLE] = f"{name} {model} ({host})"
            return True
        return False

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            if await self.async_connect(user_input[CONF_HOST], user_input[CONF_PSK]):
                self.user_input[CONF_HOST] = user_input[CONF_HOST]
                self.user_input[CONF_PSK] = user_input[CONF_PSK]
                self.user_input[CONF_EXT_SPEAKER] = user_input[CONF_EXT_SPEAKER]
                self.user_input[CONF_TIME_FORMAT] = user_input[CONF_TIME_FORMAT]
                power_status = await self.hass.async_add_executor_job(self.client.get_power_status)
                if power_status == "active":
                    return await self.async_step_source_list()
                return self.async_create_entry(
                    title=self.user_input[CONF_TITLE], data=self.user_input
                )
            errors["base"] = "no_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): cv.string,
                    vol.Required(CONF_PSK): cv.string,
                    vol.Required(CONF_EXT_SPEAKER, default=DEFAULT_EXT_SPEAKER): cv.boolean,
                    vol.Required(CONF_TIME_FORMAT, default=DEFAULT_TIME_FORMAT): vol.In([CONF_12H, CONF_24H]),
                }
            ),
            errors=errors,
        )

    async def async_step_source_list(self, user_input=None):
        if user_input is not None:
            self.user_input[CONF_SOURCE_LIST] = user_input[CONF_SOURCE_LIST]
            return await self.async_step_source_config()

        sources = await self.hass.async_add_executor_job(self.client.get_sources)
        source_names = list(sources.keys())

        return self.async_show_form(
            step_id="source_list",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SOURCE_LIST, default=source_names): cv.multi_select(source_names),
                }
            ),
        )

    async def async_step_source_config(self, user_input=None):
        if user_input is not None:
            source_config = {
                CONF_SOURCE: self.user_input[CONF_SOURCE_LIST][self.index],
                CONF_HIDDEN: False,
                CONF_NAME: user_input[CONF_NAME],
            }
            self.user_input[CONF_SOURCE_CONFIG].append(source_config)
            self.index += 1

        if self.index == len(self.user_input[CONF_SOURCE_LIST]):
            self.index = 0
            return self.async_create_entry(title=self.user_input[CONF_TITLE], data=self.user_input)
        elif self.index == 0:
            self.user_input[CONF_SOURCE_CONFIG] = []

        source = self.user_input[CONF_SOURCE_LIST][self.index]

        return self.async_show_form(
            step_id="source_config",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=source): cv.string,
                }
            ),
            description_placeholders={"source": source},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Eero options callback."""
        return SonyBraviaOptionsFlow(config_entry)


class SonyBraviaOptionsFlow(config_entries.OptionsFlow):
    """Config flow options for Eero."""

    def __init__(self, config_entry):
        """Initialize Eero options flow."""
        self.config_entry = config_entry
        self.data = config_entry.data
        self.device = None
        self.index = 0
        self.options = config_entry.options
        self.user_input = {}

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        self.device = self.hass.data[DOMAIN][self.config_entry.entry_id][DATA_COORDINATOR].data
        return await self.async_step_basic()

    async def async_step_basic(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_EXT_SPEAKER] = user_input[CONF_EXT_SPEAKER]
            self.user_input[CONF_TIME_FORMAT] = user_input[CONF_TIME_FORMAT]
            if self.device.is_on:
                return await self.async_step_source_list()
            elif self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self.user_input)

        conf_ext_speaker = self.options.get(CONF_EXT_SPEAKER, self.data.get(CONF_EXT_SPEAKER, DEFAULT_EXT_SPEAKER))
        conf_time_format = self.options.get(CONF_TIME_FORMAT, self.data.get(CONF_TIME_FORMAT, DEFAULT_TIME_FORMAT))

        return self.async_show_form(
            step_id="basic",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EXT_SPEAKER, default=conf_ext_speaker): cv.boolean,
                    vol.Required(CONF_TIME_FORMAT, default=conf_time_format): vol.In([CONF_12H, CONF_24H]),
                }
            ),
        )

    async def async_step_source_list(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SOURCE_LIST] = user_input[CONF_SOURCE_LIST]
            return await self.async_step_source_config()

        source_names = list(self.device.sources.keys())

        conf_source_list = self.options.get(CONF_SOURCE_LIST, self.data.get(CONF_SOURCE_LIST, source_names))

        return self.async_show_form(
            step_id="source_list",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SOURCE_LIST, default=conf_source_list): cv.multi_select(source_names),
                }
            ),
        )

    async def async_step_source_config(self, user_input=None):
        if user_input is not None:
            source_config = {
                CONF_SOURCE: self.user_input[CONF_SOURCE_LIST][self.index],
                CONF_HIDDEN: False,
                CONF_NAME: user_input[CONF_NAME],
            }
            self.user_input[CONF_SOURCE_CONFIG].append(source_config)
            self.index += 1

        if self.index == len(self.user_input[CONF_SOURCE_LIST]):
            self.index = 0
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self.user_input)
        elif self.index == 0:
            self.user_input[CONF_SOURCE_CONFIG] = []

        source = self.user_input[CONF_SOURCE_LIST][self.index]
        conf_name = source
        for conf in self.options.get(CONF_SOURCE_CONFIG, self.data.get(CONF_SOURCE_CONFIG, [])):
            if source == conf[CONF_SOURCE]:
                conf_name = conf[CONF_NAME]


        return self.async_show_form(
            step_id="source_config",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=conf_name): cv.string,
                }
            ),
            description_placeholders={"source": source},
        )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title="", data=self.user_input)

        default_save_responses = self.options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
        default_scan_interval = self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        default_timeout = self.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SAVE_RESPONSES, default=default_save_responses): cv.boolean,
                    vol.Required(CONF_SCAN_INTERVAL, default=default_scan_interval): vol.In(VALUES_SCAN_INTERVAL),
                    vol.Required(CONF_TIMEOUT, default=default_timeout): vol.In(VALUES_TIMEOUT),
                }
            ),
        )
