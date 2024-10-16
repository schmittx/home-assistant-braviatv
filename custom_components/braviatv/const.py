"""Constants used by the Sony TV component."""
ATTR_APP = "app"
ATTR_APP_LIST = "app_list"
ATTR_COMMAND = "command"
ATTR_COMMAND_LIST = "command_list"
ATTR_HOST = "host"
ATTR_NAME = "name"

DATA_COORDINATOR = "coordinator"

CONF_12H = "12H"
CONF_24H = "24H"
CONF_ENTRY_INDEX = "index"
CONF_EXT_SPEAKER = "ext_speaker"
CONF_HIDDEN = "hidden"
CONF_PSK = "psk"
CONF_SOURCE = "source"
CONF_SOURCE_CONFIG = "source_config"
CONF_SOURCE_LIST = "source_list"
CONF_TIME_FORMAT = "time_format"
CONF_TITLE = "title"

DEFAULT_SOURCE_CONFIG = []

DOMAIN = "braviatv"

MANUFACTURER = "Sony"

SERVICE_OPEN_APP = "open_app"
SERVICE_SEND_COMMAND = "send_command"

SOURCE_APP = "App"

STATE_ACTIVE = "active"

CONF_SAVE_RESPONSES = "save_responses"
CONF_TIMEOUT = "timeout"

VALUES_SCAN_INTERVAL = [30, 60, 120, 300, 600]
VALUES_TIMEOUT = [10, 15, 30, 45, 60]

DEFAULT_EXT_SPEAKER = False
DEFAULT_SAVE_LOCATION = f"/config/custom_components/{DOMAIN}/client/responses"
DEFAULT_SAVE_RESPONSES = False
DEFAULT_SCAN_INTERVAL = VALUES_SCAN_INTERVAL[0]
DEFAULT_TIME_FORMAT = CONF_24H
DEFAULT_TIMEOUT = VALUES_TIMEOUT[1]

UNDO_UPDATE_LISTENER = "undo_update_listener"
